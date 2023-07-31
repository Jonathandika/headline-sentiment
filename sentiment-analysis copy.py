import streamlit as st
import pandas as pd
import openai
import requests
from tqdm import tqdm
import time

openai.api_key = "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"


## STREAMLIT APP

st.title('Headline Sentiment Analysis')
st.subheader("Upload your file in Excel format")
st.text("Format Example:")

headlines = {
    "Headline": ["Apple's new iPhone 12 is a big hit", "Apple is releasing Vision Pro in 2023", "Apple iPhone 15 Pro is the next major release"],
}
df_apple = pd.DataFrame(headlines)
st.dataframe(df_apple)

COMPANY_NAME = st.text_input("Enter Company Name", "Apple")
ROLE = st.text_input("Enter Role", 'Media Analyst')

## FUNCTIONS

COMPANY_INFO = f'''

    {COMPANY_NAME} is a Chinese multinational technology company.
    It operates primarily in the telecommunications equipment and consumer electronics industries.
    Its product lines include tablets, laptops, wearables, and other smart devices.

'''

system_prompt = f'''

    Forget all your previous instructions.
    Pretend you are a {ROLE} working for '{COMPANY_NAME}' analyzing news headlines related to {COMPANY_NAME}.
    You need to determine whether the news article is positive, negative, or neutral in terms of its impact on {COMPANY_NAME}.

    You should relate your news headlines analysis to the industry which {COMPANY_NAME} operates in.
    {COMPANY_INFO}

'''

user_prompt = f'''

    Analyze the news headlines and determine if the sentiment is: positive, negative or neutral for the company {COMPANY_NAME}.
    Return only a single word, either "POSITIVE", "NEGATIVE" or "NEUTRAL".
    Provide a clear and definitive answer towards positive or negative sentiment, minimizing neutral output.
    Then after a '||' seperator explain shortly why the sentiment is positive, negative, or neutral.
    Ensure that your analysis is accurate and based on factual information.

'''

def detect_sentiment_w_reason(text, temp = 1, p = 1):
    """ Prints what the sentiment of the text.

        Parameters
        ----------

        temp : int, optional
            What sampling temperature to use, between 0 and 2.
            Higher values like 0.8 will make the output more random,
            while lower values like 0.2 will make it more focused and deterministic

        p : int, optional
            An alternative to sampling with temperature, called nucleus sampling,
            where the model considers the results of the tokens with top_p probability mass.
            So 0.1 means only the tokens comprising the top 10% probability mass are considered.

      """

    retries = 3
    sentiment = None

    while retries > 0:

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt + f"These are the headlines: {text}"}
        ]

        completion = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = messages,
            # max_tokens = 3,
            # n = 1,
            stop = None,
            temperature = temp,
            top_p = p
        )

        response_text = completion.choices[0].message.content

        try:
            sentiment, reason = response_text.split(" || ")
            return sentiment, reason
        except:
            retries -= 1
            continue

    else:
        return "error", "error"

# ====================

st.divider()
st.subheader("Test Sentiment Analysis")

text = st.text_area("Enter Headline", "Apple's new iPhone 12 is a big hit")
if st.button("Analyze"):
    sentiment, reason = detect_sentiment_w_reason(text)
    st.text("Sentiment: {}".format(sentiment))
    st.text_area("Reason", reason, disabled=True)

st.divider()

uploaded_file = st.file_uploader("Upload your headlines in Excel format here", type=['xlsx'])

if st.button("Analyze Headlines"):
    if uploaded_file is None or COMPANY_NAME == "":
        if uploaded_file is None:
            st.error("Please upload an Excel file")
        if COMPANY_NAME == "":
            st.error("Please enter a company name")
        if ROLE == "":
            st.error("Please enter a role")

    else:
        try:
            df = pd.read_excel(uploaded_file)
            df = df.drop_duplicates(subset=['Headline'])

            st.text("Successfully uploaded headlines")
            st.text("Number of headlines: {}".format(len(df)))
            st.dataframe(df['Headline'].head(5))

            progress_text = "Analyzing Sentiment. Please wait. This may take a while..."
            my_bar = st.progress(0, text=progress_text)

           
            result = {
                "Headline" : [],
                "Sentiment" : [],
                "Reason" : []
            }

            temp = {
                "Headline" : [],
                "Sentiment" : [],
                "Reason" : []
            }

            index = 0

            while index < len(df):
                text = df['Headline'].iloc[index:index + 100].tolist()

                try:
                    for i in range(len(text)):
                        sentiment, reason = detect_sentiment_w_reason(text[i])
                        temp["Sentiment"].append(sentiment)
                        temp["Reason"].append(reason)
                        temp["Headline"].append(text[i])
                        my_bar.progress((i+1)/len(text)*100, text=progress_text + f" ({i+1}/{len(text)})")

                except:
                    for key in temp:
                        temp[key].clear()
                        time.sleep(30)
                        continue

                else:
                    for key in result:
                        result[key].extend(temp[key])
                    for key in temp:
                        temp[key].clear()
                    index += 100
                    time.sleep(3)

            else:
                text = df['Headline'].iloc[index:len(df)].tolist()

                while True:
                    try:
                        for i in range(len(text)):
                            sentiment, reason = detect_sentiment_w_reason(text[i])
                            temp["Sentiment"].append(sentiment)
                            temp["Reason"].append(reason)
                            temp["Headline"].append(text[i])
                            my_bar.progress((i+1)/len(text)*100, text=progress_text)
                            st.text(i)

                    except:
                        for key in temp:
                            temp[key].clear()
                        time.sleep(30)
                        pass

                    else:
                        for key in result:
                            result[key].extend(temp[key])
                        break
                    break

            df_res_reason = pd.DataFrame(result)
            
            st.success('Sentiment Analysis Successful')

            @st.cache
            def convert_df(df):
                return df.to_csv().encode('utf-8')

            csv = convert_df(df_res_reason)

            st.download_button(
                label="Download Sentiment Result as CSV",
                data=csv,
                file_name='headline_sentiment.csv',
                mime='text/csv',
            )
            
            st.subheader("Headline Sentiment Result")
            st.dataframe(df_res_reason)
            
        except Exception as e:
            st.error("Something went wrong...")




