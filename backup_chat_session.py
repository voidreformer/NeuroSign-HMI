import os
import sys
import shutil
import json
import re
import zipfile

def clean_text(text: str) -> str:
    """Removes internal XML tags, metadata, and redacts sensitive API tokens."""
    text = re.sub(r"<USER_REQUEST>(.*?)</USER_REQUEST>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", text, flags=re.DOTALL)
    text = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", text, flags=re.DOTALL)
    text = re.sub(r"<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>", "", text, flags=re.DOTALL)
    # Redact GitHub tokens for security
    text = re.sub(r"ghp_[A-Za-z0-9_]+", "[REDACTED_GITHUB_TOKEN]", text)
    return text.strip()

def backup_session():
    # All conversation IDs for NeuroSign-HMI
    conv_ids = [
        "96e0957c-f014-47d1-8afe-2fa91b1c8ba7",  # Part 1: Initial Architecture & Hardware Integration
        "94f52ba6-a62e-4369-98bb-02375d81cd66"   # Part 2: 15 3D Blender Signs, 11 Indic Langs, Web Portal & Reports
    ]
    
    base_brain_dir = r"C:\Users\DSC PURULIA\.gemini\antigravity-ide\brain"
    out_md = r"E:\NeuroSign_HMI\CONVERSATION_EXPORT.md"
    dest_folder = r"E:\Antigravity_Chat_Session_NeuroSign"
    os.makedirs(dest_folder, exist_ok=True)
    
    all_messages = []

    for idx, conv_id in enumerate(conv_ids, 1):
        brain_src = os.path.join(base_brain_dir, conv_id)
        log_path = os.path.join(brain_src, ".system_generated", "logs", "transcript_full.jsonl")
        
        session_messages = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue
                    step_type = data.get("type")
                    content = data.get("content", "")
                    
                    if step_type == "USER_INPUT" and content:
                        clean = clean_text(content)
                        if clean and not clean.startswith("{{ CHECKPOINT"):
                            session_messages.append(("User", clean))
                    elif step_type == "PLANNER_RESPONSE" and content:
                        clean = clean_text(content)
                        if clean:
                            session_messages.append(("AI Assistant (Antigravity)", clean))

        all_messages.append((conv_id, idx, session_messages))

        # Copy raw brain files to Pendrive
        if os.path.exists(brain_src):
            target_conv_dir = os.path.join(dest_folder, conv_id)
            os.makedirs(target_conv_dir, exist_ok=True)
            for root, dirs, files in os.walk(brain_src):
                rel = os.path.relpath(root, brain_src)
                target_dir = os.path.join(target_conv_dir, rel)
                os.makedirs(target_dir, exist_ok=True)
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_dir, file)
                    shutil.copy2(src_file, dst_file)

    # 1. Write Combined Clean Markdown CONVERSATION_EXPORT.md
    with open(out_md, "w", encoding="utf-8") as out:
        out.write("# 💬 NeuroSign-HMI: Complete Full Chat & Conversation Transcript\n\n")
        out.write("**Project:** NeuroSign-HMI — Edge-Native Physical AI Assistive Station  \n")
        out.write("**Platform:** Antigravity IDE / Gemini Advanced Agentic Coding  \n")
        out.write(r"**Workspace Path:** `E:\NeuroSign_HMI`  \n")
        out.write(f"**Total Conversation Parts:** {len(conv_ids)}  \n\n---\n\n")

        for conv_id, part_num, msgs in all_messages:
            out.write(f"# ═════════════════════════════════════════════════════════════════\n")
            out.write(f"# SESSION PART {part_num} (Conversation ID: `{conv_id}`)\n")
            out.write(f"# ═════════════════════════════════════════════════════════════════\n\n")
            for sender, text in msgs:
                icon = "👤" if sender == "User" else "🤖"
                out.write(f"### {icon} {sender}\n\n{text}\n\n---\n\n")

    print(f"\n[1/3] Generated Complete Sanitized Markdown: {out_md} ({os.path.getsize(out_md)} bytes)")

    # 2. Write HOW_TO_RESTORE_CHAT.txt on Pendrive E:\
    readme_path = r"E:\HOW_TO_RESTORE_CHAT.txt"
    with open(readme_path, "w", encoding="utf-8") as rf:
        rf.write("=============================================================================\n")
        rf.write("NEUROSIGN-HMI: HOW TO CONTINUE THIS CHAT SESSION ON ANY PC OR WORKSTATION\n")
        rf.write("=============================================================================\n\n")
        rf.write("METHOD 1: Instant Context Resume in Chat (Easiest & Recommended)\n")
        rf.write("-----------------------------------------------------------------------------\n")
        rf.write("1. Plug this Pendrive into your PC.\n")
        rf.write("2. Open the project folder (E:\\NeuroSign_HMI) in Antigravity IDE / VS Code.\n")
        rf.write("3. Start a new Chat prompt and write:\n")
        rf.write('   "Please read @CONVERSATION_EXPORT.md and let\'s continue our work."\n')
        rf.write("4. The AI will instantly load 100% full memory of all 15 gestures, 3D Blender assets,\n")
        rf.write("   11 Indic language engines, neural training, and firmware wiring history.\n\n")
        rf.write("METHOD 2: Full Antigravity Brain Session Restore\n")
        rf.write("-----------------------------------------------------------------------------\n")
        rf.write("1. In this Pendrive, navigate to 'Antigravity_Chat_Session_NeuroSign'.\n")
        rf.write("2. Copy the conversation folder (94f52ba6-a62e-4369-98bb-02375d81cd66).\n")
        rf.write("3. On your target PC, paste it into:\n")
        rf.write("   C:\\Users\\<Username>\\.gemini\\antigravity-ide\\brain\\\n")
        rf.write("4. When you open Antigravity IDE, it will load the exact original timeline.\n\n")
        rf.write("=============================================================================\n")
    print(f"[2/3] Created Restoration Guide: {readme_path}")
    print("\n[3/3] *** SUCCESS: All Chat Sessions Successfully Backed Up to Pendrive (E:)! ***\n")

if __name__ == "__main__":
    backup_session()
