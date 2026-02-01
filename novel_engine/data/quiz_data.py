from novel_engine.data.database import Subject

class QuizDatabase:
    # 经典题库
    BANK = {
        "集合的概念与表示": {"type": "填空", "q": "A={x | ax² + 2x + 1 = 0} 只有一个元素...", "a": "0, 1", "logic": "讨论 a=0"},
        "函数的单调性": {"type": "证明", "q": "证明 f(x)=x+1/x 的单调性...", "a": "x > 1", "logic": "作差法"}
    }

    @staticmethod
    def get_quiz(subject, topic):
        if topic in QuizDatabase.BANK:
            return QuizDatabase.BANK[topic]
        
        # 如果题库没有，由于 BeingEngine 无法直接异步调 AI，
        # 我们在这里返回一个指令，让 main.py 看到这个指令后去调 AI
        return {
            "type": "AI_GENERATED",
            "subject": subject,
            "topic": topic
        }