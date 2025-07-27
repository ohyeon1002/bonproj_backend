# def save_user_solved_many_qnas(
#     submitted_qnas: ManyOdaps, current_user: User, db: Session
# ):
#     try:
#         user = user_crud.read_one_user(current_user.username, db)
#         if user is None:
#             raise HTTPException(
#                 status_code=401, detail="This feature is only for singned users"
#             )
#         gichulqna_id_list = [odap.gichulqna_id for odap in submitted_qnas.odaps]
#         correct_answer = gichulqna_crud.read_correct_answers(gichulqna_id_list, db)
#         if correct_answer is None:
#             pass
#         subject_scores = score_answers(submitted_qnas, correct_answer)
#         odaplist = [
#             Odap(
#                 choice=odap.choice,
#                 gichulqna_id=odap.gichulqna_id,
#                 odapset_id=submitted_qnas.odapset_id,
#             )
#             for odap in submitted_qnas.odaps
#         ]
#         odap_crud.create_many_odaps(odaplist, db)
#         db.commit()
#     except:
#         db.rollback()
#         raise HTTPException(404)
#     return subject_scores
