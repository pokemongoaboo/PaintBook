import streamlit as st
import openai
import time
import requests
from io import BytesIO
from PIL import Image
import re

# 設置 OpenAI API 密鑰
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 初始化 session_state
if 'story' not in st.session_state:
    st.session_state.story = None
if 'image_prompts' not in st.session_state:
    st.session_state.image_prompts = None
if 'first_image' not in st.session_state:
    st.session_state.first_image = None
if 'stage' not in st.session_state:
    st.session_state.stage = 'input'

def generate_plot_points(character, theme):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個創意十足的兒童故事作家。請確保所有內容都適合兒童。"},
            {"role": "user", "content": f"為一個關於{character}的{theme}故事生成5個可能的故事轉折點。請確保內容適合兒童，避免任何暴力、恐怖或不適當的元素。每點不超過15個字。"}
        ]
    )
    plot_points = response.choices[0].message['content'].split('\n')
    return [point.strip('1234567890. ') for point in plot_points if point.strip()]

def generate_story(character, theme, plot_point, pages):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個暢銷的童書繪本作家，擅長以孩童的純真眼光看這世界，製作出許多溫馨、積極的作品。"},
            {"role": "user", "content": f"請以'{theme}'為主題發想一個關於'{character}'的故事，在{pages}頁的篇幅內，並在倒數第三頁加入'{plot_point}'的元素。故事需要有溫馨、快樂的結局，確保內容適合兒童，避免任何暴力、恐怖或不適當的元素。請提供簡要的故事大綱。"}
        ]
    )
    return response.choices[0].message['content']

def generate_image_prompts(story, pages):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個專業的兒童繪本插畫描述師，擅長將故事轉化為生動、適合兒童的圖像描述。"},
            {"role": "user", "content": f"基於以下故事，為{pages}頁的兒童繪本創作圖像提示。每個提示應該簡潔但富有視覺細節，包括場景、角色動作和情緒。確保所有描述都適合兒童，避免任何可能被視為不適當或危險的內容。故事：{story}"}
        ]
    )
    prompts = response.choices[0].message['content'].split('\n')
    return [prompt.strip('1234567890. ') for prompt in prompts if prompt.strip()]

def safe_prompt(prompt):
    # 移除可能觸發安全系統的詞語
    unsafe_words = ["naked", "nude", "blood", "gore", "violence", "weapon", "dead", "kill"]
    for word in unsafe_words:
        prompt = re.sub(r'\b' + word + r'\b', '', prompt, flags=re.IGNORECASE)
    
    # 添加安全限定詞
    safe_prompt = f"Safe, child-friendly illustration: {prompt}. Ensure the image is suitable for young children."
    return safe_prompt

def generate_image(prompt, size="1024x1024", model="dall-e-3", max_retries=3):
    safe_prompt_text = safe_prompt(prompt)
    for attempt in range(max_retries):
        try:
            response = openai.Image.create(
                model=model,
                prompt=safe_prompt_text,
                n=1,
                size=size
            )
            image_url = response['data'][0]['url']
            return Image.open(BytesIO(requests.get(image_url).content))
        except Exception as e:
            if attempt == max_retries - 1:
                st.error(f"圖像生成失敗：{str(e)}")
                return None
            else:
                st.warning(f"圖像生成失敗，正在重試...（第{attempt+1}次）")
                time.sleep(2)  # 等待一段時間後重試

def main():
    st.title("互動式兒童繪本生成器")

    if st.session_state.stage == 'input':
        # 步驟1：選擇主角
        character_options = ["小貓", "小狗", "小兔", "小鳥", "小熊"]
        character = st.selectbox("選擇或輸入繪本主角", character_options + ["其他"])
        if character == "其他":
            character = st.text_input("請輸入自定義主角")

        # 步驟2：選擇主題
        theme_options = ["友誼", "勇氣", "幫助他人", "學習新事物", "家庭"]
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
                st.session_state.story = generate_story(character, theme, plot_point, pages)
                st.session_state.image_prompts = generate_image_prompts(st.session_state.story, pages)
                st.session_state.first_image = generate_image(st.session_state.image_prompts[0], size="1024x1024", model="dall-e-3")
                st.session_state.stage = 'preview'
                st.experimental_rerun()

    elif st.session_state.stage == 'preview':
        st.write("故事大綱預覽：")
        st.write(st.session_state.story)

        st.write("圖像提示預覽：")
        for i, prompt in enumerate(st.session_state.image_prompts):
            st.write(f"第{i+1}頁：{prompt}")

        st.write("第一張圖片預覽：")
        if st.session_state.first_image:
            st.image(st.session_state.first_image)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("重新生成"):
                st.session_state.stage = 'input'
                st.experimental_rerun()
        with col2:
            if st.button("確認並生成完整繪本"):
                st.session_state.stage = 'generate'
                st.experimental_rerun()

    elif st.session_state.stage == 'generate':
        st.write("正在生成完整繪本...")
        for i, prompt in enumerate(st.session_state.image_prompts):
            st.write(f"生成第{i+1}頁...")
            image = generate_image(prompt, size="1024x1024", model="dall-e-3")
            if image:
                st.image(image)
            time.sleep(2)  # 為了避免超過API速率限制

        st.success("繪本生成完成！")
        if st.button("重新開始"):
            st.session_state.stage = 'input'
            st.session_state.story = None
            st.session_state.image_prompts = None
            st.session_state.first_image = None
            st.experimental_rerun()

if __name__ == "__main__":
    main()
