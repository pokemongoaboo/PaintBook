import streamlit as st
import openai
import time
import requests
from io import BytesIO
from PIL import Image

# 設置OpenAI API密鑰
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ... [之前的代碼保持不變] ...

def generate_image(prompt, size="1024x1024", model="dall-e-3"):
    try:
        response = openai.Image.create(
            model=model,
            prompt=prompt,
            n=1,
            size=size
        )
        image_url = response['data'][0]['url']
        return Image.open(BytesIO(requests.get(image_url).content))
    except Exception as e:
        st.error(f"圖像生成失敗：{str(e)}")
        return None

def main():
    st.title("互動式繪本生成器")

    # ... [之前的代碼保持不變] ...

    if st.button("生成繪本"):
        with st.spinner("正在生成繪本..."):
            # ... [之前的代碼保持不變] ...

            st.write("生成第一張圖片預覽：")
            first_image = generate_image(image_prompts[0], size="1024x1024", model="dall-e-3")
            if first_image:
                st.image(first_image)

        # ... [之前的代碼保持不變] ...

        if st.button("確認並生成完整繪本"):
            with st.spinner("正在生成完整繪本..."):
                for i, prompt in enumerate(image_prompts):
                    st.write(f"生成第{i+1}頁...")
                    image = generate_image(prompt, size="1024x1024", model="dall-e-3")
                    if image:
                        st.image(image)
                    time.sleep(1)  # 為了避免超過API速率限制

            st.success("繪本生成完成！")

if __name__ == "__main__":
    main()
