# Python ইমেজ ব্যবহার করা
FROM python:3.9-slim

# সার্ভারে FFmpeg ইনস্টল করা (High Quality ভিডিওর জন্য জরুরি)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ওয়ার্কিং ডিরেক্টরি সেট করা
WORKDIR /app

# সব ফাইল কপি করা
COPY . .

# পাইথন লাইব্রেরি ইনস্টল করা
RUN pip install --no-cache-dir -r requirements.txt

# পোর্ট এক্সপোজ করা (Render এর জন্য জরুরি)
EXPOSE 10000

# অ্যাপ রান করার কমান্ড (Gunicorn সার্ভার ব্যবহার করে)
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app", "--timeout", "600"]