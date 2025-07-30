from typing import Optional
from google import genai
from google.genai import types
from textwrap import dedent

from sqlmodel import Session
from ..models import User
from ..core.config import settings
from ..crud import chat_crud


gemApikey = settings.GEMINI_APIKEY

client = genai.Client(api_key=gemApikey)


async def stream_save_gemini_chat(
    current_user: Optional[User],
    user_prompt: Optional[str],
    img_content: Optional[bytes],
    img_mime_type: Optional[str],
    db: Session,
):
    prompt_to_save = user_prompt if user_prompt else "[이미지 질문]"
    new_chat = chat_crud.create_one_chat(current_user, db)
    user_contents = []
    new_chat_turn = chat_crud.create_one_chat_turn(
        chat_id=new_chat.id, prompt=prompt_to_save, db=db
    )
    new_chat_turn.turn_num = 1 if not new_chat_turn.turn_num else +1
    if user_prompt:
        user_contents.append(user_prompt)
    if img_content:
        image_blob = types.Blob(mime_type=img_mime_type, data=img_content)
        image_part = types.Part(inline_data=image_blob)
        user_contents.append(image_part)
    if not user_contents:
        yield "data: 질문이나 이미지를 입력해 주세요.\n\n"
        return
    full_response = []
    try:
        modelResponse = await client.aio.models.generate_content_stream(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=dedent(
                    """   Role: AI assistant for the Korean navigator's exam (해기사).
                                                Core Instructions:
                                                    Input: Text only. Action: Answer the user's question.
                                                    Input: Image only. Action: Provide a detailed description of the image, focusing on maritime elements.
                                                    Input: Text and Image. Action: Answer the user's question, using the image as the primary context for your response.
                                                Output Constraints:
                                                    Language: Must be Korean.
                                                    Length: Maximum 700 characters."""
                ),
                temperature=0.3,
            ),
            contents=user_contents,
        )

        async for chunk in modelResponse:
            full_response.append(chunk.text)
            yield f"data: {chunk.text}\n\n"
    except Exception as e:
        print(e)
        yield f"data: 에러 발생 - AI 예외 발생 {e} \n\n"

    final_response_text = "".join(full_response)
    new_chat_turn.response = final_response_text
    db.commit()


async def diagReq(wrong: str, examresults: str, current_user: User):
    modelResponse = await client.aio.models.generate_content_stream(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=dedent(
                f"""
                            당신은 MarinAI의 학습 분석 엔진입니다. MarinAI는 해기사 국가자격시험을 준비하는 {current_user.indivname}님을 위한 AI 기반 진단 보고서를 제공하는 스마트 학습 서비스입니다.
                            contents로 주어지는 오답노트와 시험 결과 데이터를 기반으로 아래 기준에 따라 공식 진단 보고서를 생성해 주세요.

                            ## 작성 목적  
                            - 사용자가 자신의 취약 영역을 파악하고, 학습 전략을 재정비할 수 있도록 명확한 피드백을 제공합니다.
                            
                            ## 작성 지침  
                            - **전문성**: 해기사 교육 및 실무 경험이 반영된 조언을 제공하세요.  
                            - **문체**: 공식 보고서 스타일의 객관적이고 신뢰감 있는 문장 사용.  
                            - **형식**: Markdown으로 작성 (섹션 제목은 ##, 목록은 - 사용).  
                            - **분량**: 각 항목당 3~5줄 이내로 간결하게 정리.  
                            - **어투**: MarinAI가 분석 결과를 제공하는 형태로 작성 (ex. "MarinAI는 다음과 같이 분석합니다.")  
                            - **도입부/결론**: 교관이 아닌 시스템(MarinAI) 이름으로 시작하고 마무리할 것.
                            
                            ## 출력 예시
                                
                            ## 1. 자주 틀리는 개념 또는 문제 유형  
                            - 항해법 중 선박 통항 우선순위 관련 문항에서 반복적인 실수가 있음  
                            - 기관기기의 구조 및 원리 개념 이해 부족이 다수 확인됨
                            
                            ## 2. 전반적인 학습 상태 진단  
                            - 기본 개념은 숙지했으나, 실전 적용 능력이 부족한 편  
                            - 일부 과목에서 과도한 시간 분배로 인해 전체 점수에 영향 발생
                            
                            ## 3. 보완이 필요한 영역 및 학습 전략 제안  
                            - 자주 실수하는 개념은 플래시카드나 짧은 반복 학습으로 보완할 것  
                            - 실전 모의고사를 통해 시간 관리 능력을 점검할 것  
                            - 특히 법규 과목은 판례와 사례 중심 학습을 병행하면 효과적임

                            
                            이 형식과 내용을 기준으로 {current_user.indivname}님에게 최적화된 진단 보고서를 작성해 주세요.
                            """
            ),
            temperature=0.3,
        ),
        contents=[f"오답노트: {wrong}", f"시험 결과: {examresults}"],
    )

    async for chunk in modelResponse:
        yield f"data: {chunk.text}\n\n"


def retrieve_chat_sessions(current_user: User, db: Session):
    return chat_crud.read_chats(current_user, db)
