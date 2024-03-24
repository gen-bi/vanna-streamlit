import time
import streamlit as st
from code_editor import code_editor
from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore

st.set_page_config(layout="wide")

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn = MyVanna(config={'api_key': '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', 'model': 'gpt-3.5-turbo'})

st.sidebar.title("Output Settings")
st.sidebar.checkbox("Show SQL", value=True, key="show_sql")
st.sidebar.checkbox("Show Table", value=True, key="show_table")
st.sidebar.checkbox("Show Plotly Code", value=True, key="show_plotly_code")
st.sidebar.checkbox("Show Chart", value=True, key="show_chart")
st.sidebar.checkbox("Show Follow-up Questions", value=True, key="show_followup")

st.title("Vanna AI")
st.sidebar.write(st.session_state)


def set_question(question):
    st.session_state["my_question"] = question


assistant_message_suggested = st.chat_message(
    "assistant", avatar="https://ask.vanna.ai/static/img/vanna_circle.png"
)
if assistant_message_suggested.button("Click to show suggested questions"):
    st.session_state["my_question"] = None
    questions = vn.generate_questions()
    for i, question in enumerate(questions):
        time.sleep(0.05)
        button = st.button(
            question,
            on_click=set_question,
            args=(question,),
        )

my_question = st.session_state.get("my_question", default=None)

if my_question is None:
    my_question = st.chat_input(
        "Ask me a question about your data",
    )


if my_question:
    st.session_state["my_question"] = my_question
    user_message = st.chat_message("user")
    user_message.write(f"{my_question}")

    sql = vn.generate_sql(question=my_question)

    if sql:
        if st.session_state.get("show_sql", True):
            assistant_message_sql = st.chat_message(
                "assistant", avatar="https://ask.vanna.ai/static/img/vanna_circle.png"
            )
            assistant_message_sql.code(sql, language="sql", line_numbers=True)

        user_message_sql_check = st.chat_message("user")
        user_message_sql_check.write(f"Are you happy with the generated SQL code?")
        with user_message_sql_check:
            happy_sql = st.radio(
                "Happy",
                options=["", "yes", "no"],
                key="radio_sql",
                index=0,
            )

        if happy_sql == "no":
            st.warning(
                "Please fix the generated SQL code. Once you're done hit Shift + Enter to submit"
            )
            sql_response = code_editor(sql, lang="sql")
            fixed_sql_query = sql_response["text"]

            if fixed_sql_query != "":
                df = vn.run_sql(sql=fixed_sql_query)
            else:
                df = None
        elif happy_sql == "yes":
            df = vn.run_sql(sql=sql)
        else:
            df = None

        if df is not None:
            st.session_state["df"] = df

        if st.session_state.get("df") is not None:
            if st.session_state.get("show_table", True):
                df = st.session_state.get("df")
                assistant_message_table = st.chat_message(
                    "assistant",
                    avatar="https://ask.vanna.ai/static/img/vanna_circle.png",
                )
                if len(df) > 10:
                    assistant_message_table.text("First 10 rows of data")
                    assistant_message_table.dataframe(df.head(10))
                else:
                    assistant_message_table.dataframe(df)

            code = vn.generate_plotly_code(question=my_question, sql=sql, df=df)

            if st.session_state.get("show_plotly_code", False):
                assistant_message_plotly_code = st.chat_message(
                    "assistant",
                    avatar="https://ask.vanna.ai/static/img/vanna_circle.png",
                )
                assistant_message_plotly_code.code(
                    code, language="python", line_numbers=True
                )

            user_message_plotly_check = st.chat_message("user")
            user_message_plotly_check.write(
                f"Are you happy with the generated Plotly code?"
            )
            with user_message_plotly_check:
                happy_plotly = st.radio(
                    "Happy",
                    options=["", "yes", "no"],
                    key="radio_plotly",
                    index=0,
                )

            if happy_plotly == "no":
                st.warning(
                    "Please fix the generated Python code. Once you're done hit Shift + Enter to submit"
                )
                python_code_response = code_editor(code, lang="python")
                code = python_code_response["text"]
            elif happy_plotly == "":
                code = None

            if code is not None and code != "":
                if st.session_state.get("show_chart", True):
                    assistant_message_chart = st.chat_message(
                        "assistant",
                        avatar="https://ask.vanna.ai/static/img/vanna_circle.png",
                    )
                    fig = vn.generate_plot(code=code, df=df)
                    if fig is not None:
                        assistant_message_chart.plotly_chart(fig)
                    else:
                        assistant_message_chart.error("I couldn't generate a chart")

                if st.session_state.get("show_followup", True):
                    assistant_message_followup = st.chat_message(
                        "assistant",
                        avatar="https://ask.vanna.ai/static/img/vanna_circle.png",
                    )
                    followup_questions = vn.generate_followup(
                        question=my_question, df=df
                    )
                    st.session_state["df"] = None

                    if len(followup_questions) > 0:
                        assistant_message_followup.text(
                            "Here are some possible follow-up questions"
                        )
                        # Print the first 5 follow-up questions
                        for question in followup_questions[:5]:
                            time.sleep(0.05)
                            assistant_message_followup.write(question)

    else:
        assistant_message_error = st.chat_message(
            "assistant", avatar="https://ask.vanna.ai/static/img/vanna_circle.png"
        )
        assistant_message_error.error("I wasn't able to generate SQL for that question")
