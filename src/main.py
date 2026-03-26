import os
import sys
import schedule
import subprocess
import asyncio
import shutil
import datetime
from uuid import uuid4
from typing import Dict, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from termcolor import colored
from prettytable import PrettyTable

# Internal imports (relative to src/ if PYTHONPATH is src)
try:
    from art import *
    from cache import *
    from utils import *
    from config import *
    from status import *
    from constants import *
    from classes.Tts import TTS
    from classes.Twitter import Twitter
    from classes.YouTube import YouTube
    from classes.Outreach import Outreach
    from classes.AFM import AffiliateMarketing
    from llm_provider import list_models, select_model, get_active_model
except ImportError:
    # Fallback for different import styles
    from src.art import *
    from src.cache import *
    from src.utils import *
    from src.config import *
    from src.status import *
    from src.constants import *
    from src.classes.Tts import TTS
    from src.classes.Twitter import Twitter
    from src.classes.YouTube import YouTube
    from src.classes.Outreach import Outreach
    from src.classes.AFM import AffiliateMarketing
    from src.llm_provider import list_models, select_model, get_active_model

app = FastAPI(title="MoneyPrinterV2 API")

# Global task tracker
tasks: Dict[str, Any] = {}

class GenerateRequest(BaseModel):
    topic: str

@app.get("/")
async def read_index():
    index_path = os.path.join(ROOT_DIR, "public", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "Frontend not found", "path": index_path})

@app.post("/api/generate")
async def generate_video_api(request: GenerateRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid4())
    tasks[task_id] = {
        "status": "Iniciando...",
        "progress": 0,
        "log": f"Iniciando projeto: {request.topic}",
        "error": False
    }
    background_tasks.add_task(run_generation_worker, task_id, request.topic)
    return {"task_id": task_id}

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.get("/api/videos")
async def list_videos():
    storage_dir = os.path.join(ROOT_DIR, "storage")
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    
    videos = []
    for f in os.listdir(storage_dir):
        if f.endswith(".mp4"):
            path = os.path.join(storage_dir, f)
            stats = os.stat(path)
            videos.append({
                "name": f,
                "size": round(stats.st_size / (1024 * 1024), 2),
                "date": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
            })
    return sorted(videos, key=lambda x: x["date"], reverse=True)

async def run_generation_worker(task_id: str, topic: str):
    try:
        # Step 1: Get Account
        tasks[task_id]["status"] = "Verificando conta..."
        tasks[task_id]["progress"] = 5
        
        cached_accounts = get_accounts("youtube")
        if not cached_accounts:
            raise Exception("Nenhuma conta YouTube configurada no cache. Configure uma via CLI primeiro.")
        
        acc = cached_accounts[0]
        
        # Step 2: Initialize
        tasks[task_id]["status"] = "Gerando Script..."
        tasks[task_id]["progress"] = 15
        
        tts = TTS()
        youtube = YouTube(
            acc["id"], acc["nickname"], acc["firefox_profile"], 
            acc["niche"], acc["language"]
        )
        
        # Override topic
        youtube.subject = topic
        tasks[task_id]["log"] = f"Tema definido: {topic}"

        # Step 3: Generation Steps (Manual for progress reporting)
        tasks[task_id]["status"] = "Criando roteiro..."
        youtube.generate_script()
        tasks[task_id]["progress"] = 30
        
        tasks[task_id]["status"] = "Gerando Locução..."
        youtube.generate_script_to_speech(tts)
        tasks[task_id]["progress"] = 45
        
        tasks[task_id]["status"] = "Criando Prompts de Imagem..."
        youtube.generate_prompts()
        tasks[task_id]["progress"] = 60
        
        tasks[task_id]["status"] = "Gerando Imagens AI..."
        for i, prompt in enumerate(youtube.image_prompts):
            tasks[task_id]["log"] = f"Gerando imagem {i+1}/{len(youtube.image_prompts)}..."
            youtube.generate_image(prompt)
            tasks[task_id]["progress"] = 60 + int((i+1)/len(youtube.image_prompts) * 20)

        tasks[task_id]["status"] = "Editando Vídeo Final..."
        tasks[task_id]["progress"] = 85
        video_path = youtube.combine()
        
        # Step 4: Finalize
        tasks[task_id]["status"] = "Movendo para o Storage..."
        tasks[task_id]["progress"] = 95
        
        storage_dir = os.path.join(ROOT_DIR, "storage")
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            
        filename = f"reels_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.mp4"
        final_dest = os.path.join(storage_dir, filename)
        
        shutil.move(video_path, final_dest)
        
        tasks[task_id]["status"] = "Concluído!"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["log"] = f"Sucesso! Vídeo salvo como {filename}"

    except Exception as e:
        tasks[task_id]["error"] = True
        tasks[task_id]["status"] = "Erro na Geração"
        tasks[task_id]["log"] = f"ERRO CRÍTICO: {str(e)}"

# Mount static files
storage_path = os.path.join(ROOT_DIR, "storage")
if not os.path.exists(storage_path):
    os.makedirs(storage_path)
app.mount("/storage", StaticFiles(directory=storage_path), name="storage")

def main():
    """Main entry point for the application, providing a menu-driven interface
    to manage YouTube, Twitter bots, Affiliate Marketing, and Outreach tasks.

    This function allows users to:
    1. Start the YouTube Shorts Automater to manage YouTube accounts, 
       generate and upload videos, and set up CRON jobs.
    2. Start a Twitter Bot to manage Twitter accounts, post tweets, and 
       schedule posts using CRON jobs.
    3. Manage Affiliate Marketing by creating pitches and sharing them via 
       Twitter accounts.
    4. Initiate an Outreach process for engagement and promotion tasks.
    5. Exit the application.

    The function continuously prompts users for input, validates it, and 
    executes the selected option until the user chooses to quit.

    Args:
        None

    Returns:
        None"""

    # Get user input
    # user_input = int(question("Select an option: "))
    valid_input = False
    while not valid_input:
        try:
    # Show user options
            info("\n============ OPTIONS ============", False)

            for idx, option in enumerate(OPTIONS):
                print(colored(f" {idx + 1}. {option}", "cyan"))

            info("=================================\n", False)
            user_input = os.getenv("OPTION", "1").strip()
            if user_input == '':
                print("\n" * 100)
                raise ValueError("Empty input is not allowed.")
            user_input = int(user_input)
            valid_input = True
        except ValueError as e:
            print("\n" * 100)
            print(f"Invalid input: {e}")


    # Start the selected option
    if user_input == 1:
        info("Starting YT Shorts Automater...")

        cached_accounts = get_accounts("youtube")

        if len(cached_accounts) == 0:
            warning("No accounts found in cache. Create one now?")
            user_input = question("Yes/No: ")

            if user_input.lower() == "yes":
                generated_uuid = str(uuid4())

                success(f" => Generated ID: {generated_uuid}")
                nickname = question(" => Enter a nickname for this account: ")
                fp_profile = question(" => Enter the path to the Firefox profile: ")
                niche = question(" => Enter the account niche: ")
                language = question(" => Enter the account language: ")

                account_data = {
                    "id": generated_uuid,
                    "nickname": nickname,
                    "firefox_profile": fp_profile,
                    "niche": niche,
                    "language": language,
                    "videos": [],
                }

                add_account("youtube", account_data)

                success("Account configured successfully!")
        else:
            table = PrettyTable()
            table.field_names = ["ID", "UUID", "Nickname", "Niche"]

            for account in cached_accounts:
                table.add_row([cached_accounts.index(account) + 1, colored(account["id"], "cyan"), colored(account["nickname"], "blue"), colored(account["niche"], "green")])

            print(table)
            info("Type 'd' to delete an account.", False)

            user_input = question("Select an account to start (or 'd' to delete): ").strip()

            if user_input.lower() == "d":
                delete_input = question("Enter account number to delete: ").strip()
                account_to_delete = None

                for account in cached_accounts:
                    if str(cached_accounts.index(account) + 1) == delete_input:
                        account_to_delete = account
                        break

                if account_to_delete is None:
                    error("Invalid account selected. Please try again.", "red")
                else:
                    confirm = question(f"Are you sure you want to delete '{account_to_delete['nickname']}'? (Yes/No): ").strip().lower()

                    if confirm == "yes":
                        remove_account("youtube", account_to_delete["id"])
                        success("Account removed successfully!")
                    else:
                        warning("Account deletion canceled.", False)

                return

            selected_account = None

            for account in cached_accounts:
                if str(cached_accounts.index(account) + 1) == user_input:
                    selected_account = account

            if selected_account is None:
                error("Invalid account selected. Please try again.", "red")
                main()
            else:
                youtube = YouTube(
                    selected_account["id"],
                    selected_account["nickname"],
                    selected_account["firefox_profile"],
                    selected_account["niche"],
                    selected_account["language"]
                )

                while True:
                    rem_temp_files()
                    info("\n============ OPTIONS ============", False)

                    for idx, youtube_option in enumerate(YOUTUBE_OPTIONS):
                        print(colored(f" {idx + 1}. {youtube_option}", "cyan"))

                    info("=================================\n", False)

                    # Get user input
                    user_input = int(question("Select an option: "))
                    tts = TTS()

                    if user_input == 1:
                        youtube.generate_video(tts)
                        upload_to_yt = question("Do you want to upload this video to YouTube? (Yes/No): ")
                        if upload_to_yt.lower() == "yes":
                            youtube.upload_video()
                    elif user_input == 2:
                        videos = youtube.get_videos()

                        if len(videos) > 0:
                            videos_table = PrettyTable()
                            videos_table.field_names = ["ID", "Date", "Title"]

                            for video in videos:
                                videos_table.add_row([
                                    videos.index(video) + 1,
                                    colored(video["date"], "blue"),
                                    colored(video["title"][:60] + "...", "green")
                                ])

                            print(videos_table)
                        else:
                            warning(" No videos found.")
                    elif user_input == 3:
                        info("How often do you want to upload?")

                        info("\n============ OPTIONS ============", False)
                        for idx, cron_option in enumerate(YOUTUBE_CRON_OPTIONS):
                            print(colored(f" {idx + 1}. {cron_option}", "cyan"))

                        info("=================================\n", False)

                        user_input = int(question("Select an Option: "))

                        cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
                        command = ["python", cron_script_path, "youtube", selected_account['id'], get_active_model()]

                        def job():
                            subprocess.run(command)

                        if user_input == 1:
                            # Upload Once
                            schedule.every(1).day.do(job)
                            success("Set up CRON Job.")
                        elif user_input == 2:
                            # Upload Twice a day
                            schedule.every().day.at("10:00").do(job)
                            schedule.every().day.at("16:00").do(job)
                            success("Set up CRON Job.")
                        else:
                            break
                    elif user_input == 4:
                        if get_verbose():
                            info(" => Climbing Options Ladder...", False)
                        break
    elif user_input == 2:
        info("Starting Twitter Bot...")

        cached_accounts = get_accounts("twitter")

        if len(cached_accounts) == 0:
            warning("No accounts found in cache. Create one now?")
            user_input = question("Yes/No: ")

            if user_input.lower() == "yes":
                generated_uuid = str(uuid4())

                success(f" => Generated ID: {generated_uuid}")
                nickname = question(" => Enter a nickname for this account: ")
                fp_profile = question(" => Enter the path to the Firefox profile: ")
                topic = question(" => Enter the account topic: ")

                add_account("twitter", {
                    "id": generated_uuid,
                    "nickname": nickname,
                    "firefox_profile": fp_profile,
                    "topic": topic,
                    "posts": []
                })
        else:
            table = PrettyTable()
            table.field_names = ["ID", "UUID", "Nickname", "Account Topic"]

            for account in cached_accounts:
                table.add_row([cached_accounts.index(account) + 1, colored(account["id"], "cyan"), colored(account["nickname"], "blue"), colored(account["topic"], "green")])

            print(table)
            info("Type 'd' to delete an account.", False)

            user_input = question("Select an account to start (or 'd' to delete): ").strip()

            if user_input.lower() == "d":
                delete_input = question("Enter account number to delete: ").strip()
                account_to_delete = None

                for account in cached_accounts:
                    if str(cached_accounts.index(account) + 1) == delete_input:
                        account_to_delete = account
                        break

                if account_to_delete is None:
                    error("Invalid account selected. Please try again.", "red")
                else:
                    confirm = question(f"Are you sure you want to delete '{account_to_delete['nickname']}'? (Yes/No): ").strip().lower()

                    if confirm == "yes":
                        remove_account("twitter", account_to_delete["id"])
                        success("Account removed successfully!")
                    else:
                        warning("Account deletion canceled.", False)

                return

            selected_account = None

            for account in cached_accounts:
                if str(cached_accounts.index(account) + 1) == user_input:
                    selected_account = account

            if selected_account is None:
                error("Invalid account selected. Please try again.", "red")
                main()
            else:
                twitter = Twitter(selected_account["id"], selected_account["nickname"], selected_account["firefox_profile"], selected_account["topic"])

                while True:
                    
                    info("\n============ OPTIONS ============", False)

                    for idx, twitter_option in enumerate(TWITTER_OPTIONS):
                        print(colored(f" {idx + 1}. {twitter_option}", "cyan"))

                    info("=================================\n", False)

                    # Get user input
                    user_input = int(question("Select an option: "))

                    if user_input == 1:
                        twitter.post()
                    elif user_input == 2:
                        posts = twitter.get_posts()

                        posts_table = PrettyTable()

                        posts_table.field_names = ["ID", "Date", "Content"]

                        for post in posts:
                            posts_table.add_row([
                                posts.index(post) + 1,
                                colored(post["date"], "blue"),
                                colored(post["content"][:60] + "...", "green")
                            ])

                        print(posts_table)
                    elif user_input == 3:
                        info("How often do you want to post?")

                        info("\n============ OPTIONS ============", False)
                        for idx, cron_option in enumerate(TWITTER_CRON_OPTIONS):
                            print(colored(f" {idx + 1}. {cron_option}", "cyan"))

                        info("=================================\n", False)

                        user_input = int(question("Select an Option: "))

                        cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
                        command = ["python", cron_script_path, "twitter", selected_account['id'], get_active_model()]

                        def job():
                            subprocess.run(command)

                        if user_input == 1:
                            # Post Once a day
                            schedule.every(1).day.do(job)
                            success("Set up CRON Job.")
                        elif user_input == 2:
                            # Post twice a day
                            schedule.every().day.at("10:00").do(job)
                            schedule.every().day.at("16:00").do(job)
                            success("Set up CRON Job.")
                        elif user_input == 3:
                            # Post thrice a day
                            schedule.every().day.at("08:00").do(job)
                            schedule.every().day.at("12:00").do(job)
                            schedule.every().day.at("18:00").do(job)
                            success("Set up CRON Job.")
                        else:
                            break
                    elif user_input == 4:
                        if get_verbose():
                            info(" => Climbing Options Ladder...", False)
                        break
    elif user_input == 3:
        info("Starting Affiliate Marketing...")

        cached_products = get_products()

        if len(cached_products) == 0:
            warning("No products found in cache. Create one now?")
            user_input = question("Yes/No: ")

            if user_input.lower() == "yes":
                affiliate_link = question(" => Enter the affiliate link: ")
                twitter_uuid = question(" => Enter the Twitter Account UUID: ")

                # Find the account
                account = None
                for acc in get_accounts("twitter"):
                    if acc["id"] == twitter_uuid:
                        account = acc

                add_product({
                    "id": str(uuid4()),
                    "affiliate_link": affiliate_link,
                    "twitter_uuid": twitter_uuid
                })

                afm = AffiliateMarketing(affiliate_link, account["firefox_profile"], account["id"], account["nickname"], account["topic"])

                afm.generate_pitch()
                afm.share_pitch("twitter")
        else:
            table = PrettyTable()
            table.field_names = ["ID", "Affiliate Link", "Twitter Account UUID"]

            for product in cached_products:
                table.add_row([cached_products.index(product) + 1, colored(product["affiliate_link"], "cyan"), colored(product["twitter_uuid"], "blue")])

            print(table)

            user_input = question("Select a product to start: ")

            selected_product = None

            for product in cached_products:
                if str(cached_products.index(product) + 1) == user_input:
                    selected_product = product

            if selected_product is None:
                error("Invalid product selected. Please try again.", "red")
                main()
            else:
                # Find the account
                account = None
                for acc in get_accounts("twitter"):
                    if acc["id"] == selected_product["twitter_uuid"]:
                        account = acc

                afm = AffiliateMarketing(selected_product["affiliate_link"], account["firefox_profile"], account["id"], account["nickname"], account["topic"])

                afm.generate_pitch()
                afm.share_pitch("twitter")

    elif user_input == 4:
        info("Starting Outreach...")

        outreach = Outreach()

        outreach.start()
    elif user_input == 5:
        if get_verbose():
            print(colored(" => Quitting...", "blue"))
        sys.exit(0)
    else:
        error("Invalid option selected. Please try again.", "red")
        main()
    

if __name__ == "__main__":
    # Print ASCII Banner
    print_banner()

    first_time = get_first_time_running()

    if first_time:
        print(colored("Hey! It looks like you're running MoneyPrinter V2 for the first time. Let's get you setup first!", "yellow"))

    # Setup file tree
    assert_folder_structure()
    if not os.path.exists(os.path.join(ROOT_DIR, "storage")):
        os.makedirs(os.path.join(ROOT_DIR, "storage"))

    # Remove temporary files
    rem_temp_files()

    # Fetch MP3 Files
    fetch_songs()

    configured_model = get_ollama_model()
    if configured_model:
        select_model(configured_model)
        success(f"Using configured model: {configured_model}")
    else:
        model_choice = os.getenv('MODEL', 'gemini-3.1-pro-preview')
        select_model(model_choice)
        success(f"Using model: {model_choice}")

    # Force system to start FastAPI (Uvicorn) directly, avoiding terminal interactive menus
    info("Starting FastAPI server directly...")
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
