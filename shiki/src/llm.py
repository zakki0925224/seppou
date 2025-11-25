from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


def create_llm_interface(
    google_api_key: str,
    google_model: str,
    local_base_url: str,
    local_model: str,
    use_local_model: bool,
) -> ChatOpenAI | ChatGoogleGenerativeAI:
    if use_local_model:
        llm = ChatOpenAI(
            api_key="lm-studio",  # dummy
            base_url=local_base_url,
            model=local_model,
        )
    else:
        llm = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            model=google_model,
        )

    return llm
