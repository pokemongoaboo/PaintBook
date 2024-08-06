import streamlit as st
import openai
import time
import requests
from io import BytesIO
from PIL import Image

# 設置OpenAI API密鑰
openai.api_key = st.secrets["OPENAI_API_KEY"]

def generate_plot_points(character, theme):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一個創意十足的兒童故事作家。"},
            {"role": "user", "content": f"為一個關於{character}的{theme}故事生成5個可能的故事轉折點。請簡潔地列出這些點，每點不超過15個字。"}
        ]
    )
    plot_points = response.choices[0].message['content'].split('\n')
    return [point.strip('1234567890. ') for point in plot_points if point.strip()]

def generate_story(character, theme, plot_point, pages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一個暢銷的童書繪本作家，擅長以孩童的純真眼光看這世界，製作出許多溫暖人心的作品。"},
            {"role": "user", "content": f"請以'{theme}'為主題發想一個關於'{character}'的故事，在{pages}頁的篇幅內，並在倒數第三頁加入'{plot_point}'的元素。故事需要有溫馨、快樂的結局。請提供簡要的故事大綱。"}
        ]
    )
    return response.choices[0].message['content']

def generate_image_prompts(story, pages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一個專業的繪本插畫描述師，擅長將故事轉化為生動的圖像描述。"},
            {"role": "user", "content": f"基於以下故事，為{pages}頁的繪本創作圖像提示。每個提示應該簡潔但富有視覺細節，包括場景、角色動作和情緒。故事：{story}"}
        ]
    )
    prompts = response.choices[0].message['content'].split('\n')
    return [prompt.strip('1234567890. ') for prompt in prompts if prompt.strip()]

def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']
    return Image.open(BytesIO(requests.get(image_url).content))

def main():
    st.title("互動式繪本生成器")

    # 步驟1：選擇主角
    character_options = ["貓咪", "狗狗", "花花", "小鳥", "小石頭"]
    character = st.selectbox("選擇或輸入繪本主角", character_options + ["其他"])
    if character == "其他":
        character = st.text_input("請輸入自定義主角")

    # 步驟2：選擇主題
    theme_options = ["親情", "友情", "冒險", "度假", "運動比賽"]
    theme = st.selectbox("選擇或輸入繪本主題", theme_options + ["其他"])
    if theme == "其他":
        theme = st.text_input("請輸入自定義主題")

    # 步驟3：生成並選擇故事轉折點
    if character and theme:
        plot_points = generate_plot_points(character, theme)
        plot_point = st.selectbox("選擇或輸入繪本故事轉折重點", plot_points + ["其他"])
        if plot_point == "其他":
            plot_point = st.text_input("請輸入自定義故事轉折重點")

    # 步驟4：選擇頁數
    pages = st.slider("選擇繪本頁數", 6, 12)

    if st.button("生成繪本"):
        with st.spinner("正在生成繪本..."):
            story = generate_story(character, theme, plot_point, pages)
            st.write("故事大綱預覽：")
            st.write(story)

            image_prompts = generate_image_prompts(story, pages)
            st.write("圖像提示預覽：")
            for i, prompt in enumerate(image_prompts):
                st.write(f"第{i+1}頁：{prompt}")

            st.write("生成第一張圖片預覽：")
            first_image = generate_image(image_prompts[0])
            st.image(first_image)

        if st.button("重新生成"):
            st.experimental_rerun()

        if st.button("確認並生成完整繪本"):
            with st.spinner("正在生成完整繪本..."):
                for i, prompt in enumerate(image_prompts):
                    st.write(f"生成第{i+1}頁...")
                    image = generate_image(prompt)
                    st.image(image)
                    time.sleep(1)  # 為了避免超過API速率限制

            st.success("繪本生成完成！")

if __name__ == "__main__":
    main()
