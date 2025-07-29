import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))


import asyncio
import time
import json
from aiolimiter import AsyncLimiter
from pathlib import Path
from app.models import (
    GichulSet,
    GichulQna,
    GichulSetType,
    GichulSetInning,
    GichulSetGrade,
    GichulSubject,
)
from app.database import engine
from app.core.config import settings
from dbcreation import main as dropcreate
from sqlmodel import Session, select, update
from google import genai
from google.genai import types


client = genai.Client(api_key="AIzaSyBjj6L3QYSD6HdQ6KoOvpg16hGB-4YoH8k")


# --- ✨ 설정값: 안전 마진 대폭 강화 ✨ ---
# 1. RPM: 10 -> 6 (60% 수준)
rate_limiter = AsyncLimiter(6, 60)
DAILY_REQUEST_LIMIT = 250
BATCH_SIZE = 10
RECOVERY_FILENAME = "gichul_explanations_recovery.json"


def create_batches(items, batch_size):
    """리스트를 정해진 크기의 배치로 나눕니다."""
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


async def geminiExplainBatch(gichulqna_batch):
    """배치된 문제들에 대한 해설을 JSON으로 요청합니다."""
    # 배치된 문제들을 프롬프트 형식에 맞게 변환
    prompt_contents = [
        {"id": qna.id, "question": qna.model_dump_json()} for qna in gichulqna_batch
    ]

    system_instruction = """당신은 해기사 시험 대비를 돕는 선생님입니다.
    다음은 여러 개의 해기사 시험 문제입니다.
    'answer' 필드의 '가', '나', '사', 또는 '아'는 각각 'ex1str', 'ex2str', 'ex3str', 'ex4str'이 정답임을 가리킵니다.
    각 문제의 id와 함께 400자 이내의 해설을 JSON 형식의 리스트로 반환해 주세요.
    각 JSON 객체는 반드시 `id`와 `explanation` 키를 가져야 합니다. 다른 말은 절대 추가하지 마세요."""

    modelResponse = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            response_mime_type="application/json",  # JSON 응답을 강제하면 더 안정적입니다.
        ),
        contents=json.dumps(prompt_contents),
    )
    return modelResponse.text


async def call_api_for_batch(gichulqna_batch):
    """배치 단위로 API를 호출하고 결과를 파싱합니다."""
    async with rate_limiter:
        batch_ids = [qna.id for qna in gichulqna_batch]
        print(f"배치 {batch_ids} 해설 생성 시작")
        try:
            response_text = await geminiExplainBatch(gichulqna_batch)
            # JSON 텍스트를 파이썬 객체로 파싱
            explanations = json.loads(response_text)
            print(f"배치 {batch_ids} 해설 생성 완료")
            return explanations
        except Exception as e:
            print(f"!!! 배치 {batch_ids} 처리 중 오류 발생: {e}")
            # 오류가 발생한 배치의 모든 문제에 대해 실패 처리
            return [{"id": q_id, "explanation": "오류 발생"} for q_id in batch_ids]


# ✨ 더 관대하고 안정적인 DB 업데이트 함수
def update_explanations_in_db(results, db_engine):
    """
    DB에 업데이트를 시도합니다. 벌크 업데이트가 실패하면 한 번에 하나씩 재시도합니다.
    """
    if not results:
        return True

    print(f"총 {len(results)}개의 문제에 대한 해설을 데이터베이스에 업데이트합니다...")

    # 1. 먼저 효율적인 벌크 업데이트를 시도합니다.
    with Session(db_engine) as session:
        try:
            update_statement = update(GichulQna)
            session.execute(update_statement, results)
            session.commit()
            print("✨ 벌크 업데이트가 성공적으로 완료되었습니다.")
            return True
        except Exception as e:
            # StaleDataError 같은 오류가 발생하면, 아래의 개별 업데이트 로직으로 넘어갑니다.
            print(f"!!! 벌크 업데이트 중 오류 발생: {e}")
            print("--- 개별 업데이트 모드로 전환하여 재시도합니다. ---")
            session.rollback()

    # 2. 벌크 업데이트가 실패했을 경우, 하나씩 업데이트를 시도합니다.
    updated_count = 0
    failed_ids = []
    with Session(db_engine) as session:
        for result in results:
            try:
                qna_id = result["id"]
                # 단일 항목에 대한 업데이트 구문
                single_update_stmt = (
                    update(GichulQna)
                    .where(GichulQna.id == qna_id)
                    .values(explanation=result["explanation"])
                )
                # exec의 반환값(Result 객체)에서 실제 영향받은 행의 수를 확인
                result_proxy = session.exec(single_update_stmt)

                if result_proxy.rowcount > 0:
                    updated_count += 1
                else:
                    # 업데이트된 행이 없으면, 해당 ID가 DB에 없는 것입니다.
                    failed_ids.append(qna_id)

            except Exception as item_error:
                # 개별 업데이트 중 다른 예외가 발생할 경우
                print(f"ID {result.get('id')} 업데이트 중 예외 발생: {item_error}")
                failed_ids.append(result.get("id", "N/A"))

        session.commit()  # 성공한 것들만 커밋

    print(
        f"✨ 개별 업데이트 완료: 총 {updated_count}개 성공, {len(failed_ids)}개 실패."
    )
    if failed_ids:
        print(f"실패한 ID 목록 (DB에 존재하지 않을 수 있음): {failed_ids}")

    # 실패한 항목이 있더라도, 나머지는 성공했으므로 True를 반환하여 복구 파일을 삭제하도록 합니다.
    return True


async def fetch_and_update_routine():
    """API 호출부터 DB 업데이트 시도까지의 정상적인 흐름을 담당합니다."""
    # 1. API 호출로 데이터 가져오기
    with Session(engine) as session:
        # 강화된 하루 처리량 제한 적용
        total_qna_limit = DAILY_REQUEST_LIMIT * BATCH_SIZE
        gichulqnas_to_process = session.exec(
            select(GichulQna)
            .where(GichulQna.explanation == None)
            .limit(total_qna_limit)
        ).all()

    if not gichulqnas_to_process:
        print("처리할 새로운 문제가 없습니다.")
        return

    batches = list(create_batches(gichulqnas_to_process, BATCH_SIZE))
    tasks = [call_api_for_batch(batch) for batch in batches]
    print(
        f"총 {len(gichulqnas_to_process)}개의 문제를 {len(tasks)}개의 배치로 API 호출을 시작합니다."
    )
    all_results_nested = await asyncio.gather(*tasks)
    all_results_flat = [
        item for sublist in all_results_nested if sublist for item in sublist
    ]
    valid_results = [
        res for res in all_results_flat if res.get("explanation") != "오류 발생"
    ]

    if not valid_results:
        print("API로부터 유효한 결과를 받아오지 못했습니다.")
        return

    print(f"총 {len(valid_results)}개의 유효한 해설을 받아왔습니다.")

    # 2. DB 업데이트 시도 및 실패 시 파일 저장
    if not update_explanations_in_db(valid_results, engine):
        print(f"DB 저장이 실패하여 '{RECOVERY_FILENAME}' 파일에 결과물을 백업합니다.")
        with open(RECOVERY_FILENAME, "w", encoding="utf-8") as f:
            json.dump(valid_results, f, ensure_ascii=False, indent=4)
        print("백업 완료. 스크립트를 다시 실행하여 DB 업데이트를 재시도하세요.")


async def main():
    """스크립트의 메인 진입점. 복구 모드 또는 정상 모드를 결정합니다."""
    # 복구 파일이 존재하는지 먼저 확인
    if os.path.exists(RECOVERY_FILENAME):
        print(f"--- 복구 모드로 시작: '{RECOVERY_FILENAME}' 파일 발견 ---")
        try:
            with open(RECOVERY_FILENAME, "r", encoding="utf-8") as f:
                results_from_file = json.load(f)

            # 파일 데이터로 DB 업데이트 시도
            if update_explanations_in_db(results_from_file, engine):
                # 성공 시 복구 파일 삭제
                os.remove(RECOVERY_FILENAME)
                print(
                    f"✅ 복구 및 업데이트 성공! '{RECOVERY_FILENAME}' 파일을 삭제했습니다."
                )
            else:
                print(
                    "복구 시도 중 DB 업데이트에 다시 실패했습니다. 스크립트를 다시 실행해주세요."
                )

        except Exception as e:
            print(f"!!! 복구 파일 처리 중 심각한 오류 발생: {e}")
    else:
        # 복구 파일이 없으면 정상적인 fetch-and-update 루틴 실행
        print("--- 정상 모드로 시작 ---")
        await fetch_and_update_routine()


if __name__ == "__main__":
    asyncio.run(main())

# def main():
#     client


# if __name__ == "__main__":
#     main()
