# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Coroutine, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import asyncio
from prisma import Prisma
from rasa_sdk.types import DomainDict
from datetime import datetime
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []


class EnrollInfor(Action):
    def name(self) -> Text:
        return "action_enroll_infor"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[Text, Any]]:

        prisma = Prisma()
        await prisma.connect()

        sender_id = tracker.current_state()['sender_id']
        user = await prisma.user.find_unique(where={'id': int(sender_id)})
        semester = await prisma.semester.find_first(
            where={
                'isCurrent': True,
            }
        )
        if (user.role == 'STUDENT'):
            enroll = await prisma.enroll.find_first(
                where={
                    'userId': int(sender_id),
                    'use': {
                        'semesterId': semester.id
                    }
                },
                include={
                    'use': {
                        'include': {
                            'topic': True
                        }
                    }
                }
            )
            if (enroll):
                if (enroll.state == 'WAIT'):
                    state = 'Chờ duyệt'
                elif (enroll.state == 'IN_PROCESS'):
                    state = 'Đang thực hiện'
                elif (enroll.state == 'DONE'):
                    state = 'Hoàn thành'
                else:
                    state = 'Đề xuất'
                if (enroll.use.topic.type == 'BASIS'):
                    type = 'Niên luận cơ sở'
                else:
                    type = 'Niên luận ngành'
                dispatcher.utter_message(text="Bạn đã đăng kí đề tài:{} \n. Trạng thái:{} \n.Loại đề tài:{}.".format(
                    enroll.use.topic.name, state, type))
            else:
                dispatcher.utter_message(text="Bạn chưa đăng kí đề tài nào cả")
        else:
            dispatcher.utter_message(text="Bạn không phải là sinh viên")
        return []


class UserInfor(Action):
    def name(self) -> Text:
        return "action_user_infor"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[Text, Any]]:

        prisma = Prisma()
        await prisma.connect()

        sender_id = tracker.current_state()['sender_id']
        user = await prisma.user.find_unique(where={'id': int(sender_id)})
        if (user.role == 'STUDENT'):
            role = 'sinh viên'
        else:
            role = 'giảng viên'
        dispatcher.utter_message(text="Bạn là {}.\nTên: {}.\nEmail: {}.".format(
            role, user.fullName, user.email))
        return []


class CreateReport(Action):
    def name(self) -> Text:
        return "action_create_report"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[Text, Any]]:
        done_job = tracker.get_slot('done_job')
        next_job = tracker.get_slot('next_job')
        promise_day = tracker.get_slot('promise_day')
        promise_day = datetime.strptime(promise_day, '%d/%m/%Y')
        prisma = Prisma()
        await prisma.connect()
        sender_id = tracker.current_state()['sender_id']
        user = await prisma.user.find_unique(where={'id': int(sender_id)})
        semester = await prisma.semester.find_first(
            where={
                'isCurrent': True,
            }
        )
        dispatcher.utter_message(text="Tạo báo cáo thành công")
        if (user.role == 'STUDENT'):
            enroll = await prisma.enroll.find_first(
                where={
                    'userId': int(sender_id),
                    'use': {
                        'semesterId': semester.id
                    }
                },
                include={
                    'use': {
                        'include': {
                            'topic': True
                        }
                    }
                }
            )
            if (enroll):
                if (enroll.state == 'IN_PROCESS'):
                    if (done_job and next_job and promise_day):
                        await prisma.report.create(
                            data={
                                'enrollId': enroll.id,
                                'doneJob': done_job,
                                'nextJob': next_job,
                                'promiseAt': promise_day
                            }
                        )
                        dispatcher.utter_message(text="Tạo báo cáo thành công")
                    else:
                        dispatcher.utter_message(
                            text="Bạn chưa nhập đủ thông tin")
                else:
                    dispatcher.utter_message(
                        text="Bạn không thể tạo báo cáo do đang được duyệt hoặc đã hoàn thành")
            else:
                dispatcher.utter_message(text="Bạn chưa đăng kí đề tài nào cả")
        else:
            dispatcher.utter_message(text="Bạn không phải là sinh viên")
        return []


class ShowLastestReport(Action):
    def name(self) -> Text:
        return "action_show_lastest_report"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[Text, Any]]:
        prisma = Prisma()
        await prisma.connect()

        sender_id = tracker.current_state()['sender_id']
        user = await prisma.user.find_unique(where={'id': int(sender_id)})
        semester = await prisma.semester.find_first(
            where={
                'isCurrent': True,
            }
        )
        if (user.role == 'STUDENT'):
            enroll = await prisma.enroll.find_first(
                where={
                    'userId': int(sender_id),
                    'use': {
                        'semesterId': semester.id
                    }
                },
                include={
                    'use': {
                        'include': {
                            'topic': True
                        }
                    }
                }
            )
            if (enroll):
                if (enroll.state == 'IN_PROCESS'):
                    report = await prisma.report.find_first(
                        where={
                            'enrollId': enroll.id
                        },
                        order={
                            'createdAt': 'desc'
                        }
                    )
                    if (report):
                        dispatcher.utter_message(text="Lần báo cáo gần nhất của bạn được tạo vào ngày {}.Công việc đã hoàn thành:{} \n. Công việc tiếp theo:{} \n Hạn hoàn thành:{}.".format(
                            report.createdAt.strftime("%d/%m/%Y"), report.doneJob, report.nextJob, report.promiseAt.strftime("%d/%m/%Y")))
                    else:
                        dispatcher.utter_message(
                            text="Bạn chưa tạo báo cáo nào cả")
                else:
                    dispatcher.utter_message(
                        text="Bạn không thể tạo báo cáo do đang được duyệt hoặc đã hoàn thành")
            else:
                dispatcher.utter_message(text="Bạn chưa đăng kí đề tài nào cả")
        else:
            dispatcher.utter_message(text="Bạn không phải là sinh viên")
        return []


class ShowLastestReportFromStudent(Action):
    def name(self) -> Text:
        return "action_show_lastest_report_from_student"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[Text, Any]]:
        prisma = Prisma()
        await prisma.connect()

        student_name = tracker.get_slot('person_name')
        student = await prisma.user.find_first(
            where={
                'fullName': student_name
            }
        )
        
        sender_id = tracker.current_state()['sender_id']
        user = await prisma.user.find_unique(where={'id': int(sender_id)})
        semester = await prisma.semester.find_first(
            where={
                'isCurrent': True,
            }
        )
        
        if (student):
            if (user.role == 'TEACHER'):
                enroll = await prisma.enroll.find_first(
                    where={
                        'userId': int(student.id),
                        'semesterId': semester.id,
                        'use': {
                            'userId': int(sender_id)
                        }
                    },
                    include={
                        'use': {
                            'include': {
                                'topic': True
                            }
                        }
                    }
                )
                if (enroll):
                    report = await prisma.report.find_first(
                        where={
                            'enrollId': enroll.id
                        },
                        order={
                            'createdAt': 'desc'
                        }
                    )
                    if (report):
                        dispatcher.utter_message(text="Lần báo cáo gần nhất của sinh viên {} được tạo vào ngày {}.Công việc đã hoàn thành:{} \n. Công việc tiếp theo:{} \n Hạn hoàn thành:{}.".format(
                            student.fullName, report.createdAt.strftime("%d/%m/%Y"), report.doneJob, report.nextJob, report.promiseAt.strftime("%d/%m/%Y")))
                    else:
                        dispatcher.utter_message(
                            text="Sinh viên chưa tạo báo cáo nào cả")
                else:
                    dispatcher.utter_message(
                        text="Bạn không phải là giảng viên hỗ trợ sinh viên này")
            else:
                dispatcher.utter_message(text="Bạn không phải là giảng viên")
        # else:
        #     dispatcher.utter_message(text="Không tìm thấy sinh viên")
        return []


class ShowEnrollFromStudent(Action):
    def name(self) -> Text:
        return "action_show_enroll_from_student"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[Text, Any]]:
        prisma = Prisma()
        await prisma.connect()

        student_name = tracker.get_slot('person_name')
        student = await prisma.user.find_first(
            where={
                'fullName': student_name
            }
        )
        sender_id = tracker.current_state()['sender_id']
        user = await prisma.user.find_unique(where={'id': int(sender_id)})
        semester = await prisma.semester.find_first(
            where={
                'isCurrent': True,
            }
        )
        if (student):
            if (user.role == 'TEACHER'):
                enroll = await prisma.enroll.find_first(
                    where={
                        'userId': int(student.id),
                        'semesterId': semester.id,
                        'use': {
                            'userId': int(sender_id)
                        }
                    },
                    include={
                        'use': {
                            'include': {
                                'topic': True
                            }
                        }
                    }
                )
                if (enroll):
                    if (enroll.state == 'WAIT'):
                        state = 'Chờ duyệt'
                    elif (enroll.state == 'IN_PROCESS'):
                        state = 'Đang thực hiện'
                    elif (enroll.state == 'DONE'):
                        state = 'Hoàn thành'
                    else:
                        state = 'Đề xuất'
                    if (enroll.use.topic.type == 'BASIS'):
                        type = 'Niên luận cơ sở'
                    else:
                        type = 'Niên luận ngành'
                    dispatcher.utter_message(text="Đề tài sinh viên {} đăng kí là: {} \n Trạng thái: {} \n Loại đề tài: {}.".format(
                        student.fullName, enroll.use.topic.name, state, type))
                else:
                    dispatcher.utter_message(
                        text="Bạn không phải là giảng viên hỗ trợ sinh viên này")
            else:
                dispatcher.utter_message(text="Bạn không phải là giảng viên")
        else:
            dispatcher.utter_message(text="Không tìm thấy sinh viên")
        return []


class AskRandomTopic(Action):
    def name(self) -> Text:
        return "action_ask_random_topic"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[Text, Any]]:
        prisma = Prisma()
        await prisma.connect()

        teacher_name = tracker.get_slot('person_name')
        topic_type = tracker.get_slot('topic')
        valid_topic_types = ['Niên luận cơ sở', 'niên luận cơ sở', 'nlcs', 'nl cơ sở', 'NLCS']
        if (topic_type in valid_topic_types):
            topic_type = 'BASIS'
        else:
            topic_type = 'MASTER'
        teacher = await prisma.user.find_first(
            where={
                'fullName': teacher_name
            }
        )
        if (teacher):
            randomUse = await prisma.use.find_first(
                where={
                    'userId': int(teacher.id),
                    'topic': {
                        'type': topic_type
                    }
                },
                include={
                    'topic': True
                },
                order={
                    'random': 'asc'
                }
            )
            if (randomUse):
                dispatcher.utter_message(text="Đề tài của giảng viên {} là {}. Mô tả đề tài: {}. Link tham khảo đề tài: {}".format(
                    teacher.fullName, randomUse.topic.name, randomUse.topic.describe, randomUse.topic.link))
            else:
                dispatcher.utter_message(
                    text="Giảng viên không có đề tài nào.")
        else:
            dispatcher.utter_message(text="Không tìm thấy giảng viên")
        return []
