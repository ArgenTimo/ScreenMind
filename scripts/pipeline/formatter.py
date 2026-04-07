from common.schemas import FinalAnswer


def format_for_telegram(final_answer: FinalAnswer) -> str:
    answer = final_answer.answer.strip()

    if final_answer.answer_kind.endswith("_code") and answer:
        language = final_answer.answer_kind.removesuffix("_code")
        if language == "text":
            return f"```\n{answer}\n```"
        return f"```{language}\n{answer}\n```"

    return answer if answer else "Could not determine the answer reliably."