import os
import uuid
import re
from flask import Flask, render_template, request, Response, stream_with_context
import yt_dlp

app = Flask(__name__, template_folder='.')

# টেম্পোরারি ফোল্ডার
DOWNLOAD_FOLDER = 'temp_downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def cleanup_file(path):
    """ ফাইল ডিলিট করার ফাংশন """
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error deleting file: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.form['url']
    unique_id = str(uuid.uuid4())
    
    # 1. টেম্পোরারি ফাইলের নাম সেট করা
    temp_path_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}_%(title)s.%(ext)s')

    try:
        # 2. কনফিগারেশন: এখন সর্বোচ্চ কোয়ালিটি নামবে
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best', # ভিডিও এবং অডিও আলাদা নামাবে (Highest Quality)
            'merge_output_format': 'mp4',         # এরপর FFmpeg দিয়ে জোড়া লাগিয়ে MP4 বানাবে
            'outtmpl': temp_path_template,
            'noplaylist': True,
            'quiet': True,
        }

        filename = None
        # 3. ডাউনলোড শুরু
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Downloading High Quality Video... Please wait.")
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
            # merge_output_format ব্যবহার করলে এক্সটেনশন চেঞ্জ হতে পারে, তাই চেক করে নিচ্ছি
            if not os.path.exists(filename):
                base = os.path.splitext(filename)[0]
                if os.path.exists(base + '.mp4'):
                    filename = base + '.mp4'
                elif os.path.exists(base + '.mkv'):
                    filename = base + '.mkv'

        # 4. জেনারেটর ফাংশন
        def generate():
            try:
                with open(filename, 'rb') as f:
                    while True:
                        chunk = f.read(4096) 
                        if not chunk:
                            break
                        yield chunk
            finally:
                cleanup_file(filename) # পাঠানো শেষে ডিলিট

        # ---------------------------------------------------------
        # STRICT FILENAME CLEANER (CRASH FIX)
        # ---------------------------------------------------------
        file_base_name = os.path.basename(filename)
        
        # ইমোজি রিমুভ: শুধুমাত্র ইংরেজি অক্ষর, সংখ্যা, ড্যাশ আর আন্ডারস্কোর রাখা হবে
        # Regex: Keep only a-z, A-Z, 0-9, -, _ and .
        clean_name = re.sub(r'[^\w\-\.]', '_', file_base_name)
        
        # নাম বেশি বড় হলে ছোট করা (30 char)
        name_part, ext_part = os.path.splitext(clean_name)
        
        # ID রিমুভ করা (ডিসপ্লের সৌন্দর্যের জন্য)
        if unique_id in name_part:
            name_part = name_part.replace(f"{unique_id}_", "")

        # ডট দিয়ে শর্ট করা
        if len(name_part) > 30:
            name_part = name_part[:30] + "..."
            
        final_filename = name_part + ext_part
        
        # কোনো কারণে নাম ফাঁকা হয়ে গেলে ডিফল্ট নাম
        if len(final_filename) < 4:
            final_filename = "video.mp4"
        # ---------------------------------------------------------

        print(f"Sending file: {final_filename}")

        return Response(stream_with_context(generate()), 
                        headers={
                            'Content-Disposition': f'attachment; filename="{final_filename}"',
                            'Content-Type': 'video/mp4'
                        })

    except Exception as e:
        print(f"Error: {e}")
        return f"<h3 style='text-align:center; color:red; font-family:sans-serif;'>Server Error: {str(e)}</h3>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)