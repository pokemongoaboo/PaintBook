import streamlit as st
from openai import OpenAI
import time

# 初始化 OpenAI 客戶端
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 定義主角和主題選項
CHARACTER_OPTIONS = ["貓咪", "狗狗", "花花", "小鳥", "小石頭"]
THEME_OPTIONS = ["親情", "友情", "冒險", "度假", "運動比賽"]

def generate_plot_points(character, theme):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個創意的故事策劃者。"},
            {"role": "user", "content": f"為一個關於{character}的{theme}故事生成3-5個可能的轉折點:"}
        ],
        max_tokens=150,
        n=1,
        temperature=0.7,
    )
    plot_points = response.choices[0].message.content.strip().split("\n")
    return [point.strip() for point in plot_points if point.strip()]

def generate_story(character, theme, plot_point, pages):
    prompt = f"""
    請你角色扮演成一個暢銷的童書繪本作家，你擅長以孩童的純真眼光看這世界，製作出許多溫暖人心的作品。
    請以下列主題: {theme}發想故事，
    在{pages}的篇幅內，
    說明一個{character}的故事，
    並注意在倒數第三頁加入{plot_point}的元素，
    最後的故事需要是溫馨、快樂的結局。
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個專業的兒童繪本作家。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        n=1,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def generate_pages(story, pages, character, theme, plot_point):
    prompt = f"""
    將以下故事大綱細分至預計{pages}個跨頁的篇幅，每頁需要包括(text, image_prompt)，
    {pages-3}(倒數第三頁)才可以出現{plot_point}，
    在這之前應該要讓{character}的{theme}世界發展故事更多元化:

    {story}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個專業的繪本編輯。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        n=1,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def generate_style_base(story):
    prompt = f"""
    基於以下故事，請思考大方向上你想要呈現的視覺效果，這是你用來統一整體繪本風格的描述，請盡量精簡，使用英文撰寫:

    {story}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是一個專業的視覺設計師。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        n=1,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def image_generation(image_prompt, style_base):
    final_prompt = f"""
    Based on the image prompt: "{image_prompt}" and the style base: "{style_base}",
    please create an image with the following characteristics:
    - Color scheme and background details that match the story's atmosphere
    - Specific style and scene details as described
    - The main character should be prominently featured with the current color, shape, and features
    - Apply at least 3 effect words (lighting effects, color tones, rendering effects, visual style)
    - Use 1 or more composition techniques for visual interest
    - Do not include any text in the image
    """
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=final_prompt,
            n=1,
            size="1792x1024",
            quality="standard",
            response_format="url"
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        st.error(f"生成圖片時發生錯誤: {str(e)}")
        return None

def main():
    st.title("互動式繪本生成器")

    # 選擇或輸入繪本主角
    character = st.selectbox("選擇繪本主角", CHARACTER_OPTIONS + ["自定義"])
    if character == "自定義":
        character = st.text_input("輸入自定義主角")

    # 選擇或輸入繪本主題
    theme = st.selectbox("選擇繪本主題", THEME_OPTIONS + ["自定義"])
    if theme == "自定義":
        theme = st.text_input("輸入自定義主題")

    # 選擇頁數
    pages = st.slider("選擇繪本頁數", 6, 12, 8)

    if st.button("生成故事轉折點"):
        with st.spinner("正在生成故事轉折點..."):
            plot_points = generate_plot_points(character, theme)
        selected_plot_point = st.selectbox("選擇故事轉折點", plot_points + ["自定義"])
        if selected_plot_point == "自定義":
            selected_plot_point = st.text_input("輸入自定義故事轉折點")

        if st.button("生成繪本"):
            with st.spinner("正在生成故事..."):
                story = generate_story(character, theme, selected_plot_point, pages)
                st.write("故事大綱：")
                st.write(story)

                pages_content = generate_pages(story, pages, character, theme, selected_plot_point)
                st.write("分頁內容：")
                st.write(pages_content)

                style_base = generate_style_base(story)
                st.write("風格基礎：")
                st.write(style_base)

            # 生成並顯示第一張圖片
            with st.spinner("正在生成第一頁預覽圖..."):
                first_page = pages_content.split("\n")[0]
                image_prompt = first_page.split("image_prompt: ")[1]
                image_url = image_generation(image_prompt, style_base)
                if image_url:
                    st.image(image_url, caption="第一頁預覽")

            if st.button("生成完整繪本"):
                for i, page in enumerate(pages_content.split("\n")):
                    if page.strip():
                        text = page.split("text: ")[1].split(" image_prompt:")[0]
                        image_prompt = page.split("image_prompt: ")[1]
                        st.write(f"第 {i+1} 頁")
                        st.write(text)
                        with st.spinner(f"正在生成第 {i+1} 頁插圖..."):
                            image_url = image_generation(image_prompt, style_base)
                            if image_url:
                                st.image(image_url, caption=f"第 {i+1} 頁插圖")
                        time.sleep(5)  # 添加延遲以避免超過 API 速率限制

if __name__ == "__main__":
    main()
