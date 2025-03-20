# -*- coding: utf-8 -*-
"""
Created on Sat Mar 15 21:22:12 2025

@author: ryleg
"""

import pygame
import random
import time
import csv
import math
import numpy as np
from pygame import mixer
from pygame import sndarray

# Initialize Pygame
pygame.init()
mixer.init(channels=1)

# Screen setup - Resizable window
WIDTH, HEIGHT = 1000, 800  # Default size
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Audiovisual Oddball Task")

# Colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
DARK_GRAY = (30, 30, 30)
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)

# Default stimulus parameters
TOTAL_TRIALS = 25
STIM_DURATION = 300
ISI = 1000
NUM_BLOCKS = 1
TARGET_PROB = 0.2
ISI_VARIES = False
STIM_TYPE = "both"

# Square for photo sensor (50x50 pixels in bottom right)
SQUARE_SIZE = 50

# Sounds
def generate_tone(frequency, duration, volume=0.5):
    sample_rate = 44100
    n_samples = int(sample_rate * duration / 1000)
    t = np.arange(n_samples) / sample_rate
    tone = volume * 32767 * np.sin(2 * math.pi * frequency * t)
    tone = np.clip(tone, -32767, 32767).astype(np.int16)
    stereo_tone = np.column_stack((tone, tone))
    sound = sndarray.make_sound(stereo_tone)
    return sound

def generate_chime(duration, base_freq, volume=0.7):
    sample_rate = 44100
    n_samples = int(sample_rate * duration / 1000)
    t = np.arange(n_samples) / sample_rate
    
    tri_wave = np.abs(np.mod(t * base_freq * 4, 2) - 1)
    tri_wave2 = np.abs(np.mod(t * (base_freq * 2) * 4, 2) - 1)
    tri_wave3 = np.abs(np.mod(t * (base_freq * 3) * 4, 2) - 1)
    
    tone = 0.5 * tri_wave + 0.3 * tri_wave2 + 0.2 * tri_wave3
    
    attack = 0.02
    decay = duration / 1000 - attack
    envelope = np.minimum(t / attack, 1) * np.exp(-t / decay * 3)
    tone = volume * 32767 * tone * envelope
    
    tone = np.clip(tone, -32767, 32767).astype(np.int16)
    stereo_tone = np.column_stack((tone, tone))
    sound = sndarray.make_sound(stereo_tone)
    return sound

# Sound definitions
standard_sound = None
target_sound = None
correct_chime = generate_chime(200, 1500)
incorrect_chime = generate_chime(200, 500)

# Fonts (scaled for default size, will adjust dynamically)
title_font = pygame.font.SysFont("Arial", 50, bold=True)
prompt_font = pygame.font.SysFont("Arial", 28, bold=True)
info_font = pygame.font.SysFont("Arial", 24)
countdown_font = pygame.font.SysFont("Arial", 80, bold=True)

# Main loop
while True:
    # Get user name
    screen.fill(DARK_GRAY)
    title_text = title_font.render("Welcome", True, CYAN)
    name_prompt = prompt_font.render("Enter your name:", True, WHITE)
    user_name = ""
    entering_name = True
    while entering_name:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and user_name:
                    entering_name = False
                elif event.key == pygame.K_BACKSPACE:
                    user_name = user_name[:-1]
                elif event.unicode.isalnum():
                    user_name += event.unicode
        
        screen.fill(DARK_GRAY)
        total_height = title_text.get_height() + name_prompt.get_height() + info_font.get_height() + 40
        start_y = (HEIGHT - total_height) // 2
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, start_y))
        screen.blit(name_prompt, (WIDTH // 2 - name_prompt.get_width() // 2, start_y + title_text.get_height() + 20))
        name_text = info_font.render(user_name + "|", True, WHITE)
        screen.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2, start_y + title_text.get_height() + name_prompt.get_height() + 40))
        pygame.display.flip()

    # Parameter input screen with checkbox and radio buttons
    parameters = [
        ("Trials per block", str(TOTAL_TRIALS)),
        ("Stimulus duration (ms)", str(STIM_DURATION)),
        ("Inter-stimulus interval (ms)", str(ISI)),
        ("Number of blocks", str(NUM_BLOCKS))
    ]
    param_values = [pair[1] for pair in parameters]
    active_param = 0
    isi_varies = ISI_VARIES
    stim_type = STIM_TYPE
    entering_params = True

    input_boxes = []
    box_width, box_height = 200, 40
    start_y = 150
    spacing = 70
    for i in range(len(parameters)):
        y_pos = start_y + i * spacing
        input_boxes.append(pygame.Rect(WIDTH // 2 - box_width // 2, y_pos + 30, box_width, box_height))
    
    checkbox_rect = pygame.Rect(WIDTH // 2 + box_width // 2 + 10, start_y + 2 * spacing + 30, 20, 20)
    radio_rects = [
        pygame.Rect(WIDTH // 2 - 150, start_y + 4 * spacing + 30, 20, 20),  # Both
        pygame.Rect(WIDTH // 2 - 50, start_y + 4 * spacing + 30, 20, 20),   # Audio
        pygame.Rect(WIDTH // 2 + 50, start_y + 4 * spacing + 30, 20, 20)    # Visual
    ]

    while entering_params:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                # Recalculate positions
                input_boxes = []
                for i in range(len(parameters)):
                    y_pos = start_y + i * spacing
                    input_boxes.append(pygame.Rect(WIDTH // 2 - box_width // 2, y_pos + 30, box_width, box_height))
                checkbox_rect = pygame.Rect(WIDTH // 2 + box_width // 2 + 10, start_y + 2 * spacing + 30, 20, 20)
                radio_rects = [
                    pygame.Rect(WIDTH // 2 - 150, start_y + 4 * spacing + 30, 20, 20),
                    pygame.Rect(WIDTH // 2 - 50, start_y + 4 * spacing + 30, 20, 20),
                    pygame.Rect(WIDTH // 2 + 50, start_y + 4 * spacing + 30, 20, 20)
                ]
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, box in enumerate(input_boxes):
                    if box.collidepoint(event.pos):
                        active_param = i
                if checkbox_rect.collidepoint(event.pos):
                    isi_varies = not isi_varies
                if radio_rects[0].collidepoint(event.pos):
                    stim_type = "both"
                elif radio_rects[1].collidepoint(event.pos):
                    stim_type = "audio"
                elif radio_rects[2].collidepoint(event.pos):
                    stim_type = "visual"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    active_param = (active_param + 1) % len(parameters)
                elif event.key == pygame.K_RETURN and all(param_values):
                    entering_params = False
                elif event.key == pygame.K_BACKSPACE:
                    param_values[active_param] = param_values[active_param][:-1]
                elif event.unicode.isdigit():
                    param_values[active_param] += event.unicode

        screen.fill(DARK_GRAY)
        pygame.draw.rect(screen, BLACK, (WIDTH // 4, 50, WIDTH // 2, HEIGHT - 100), 5)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 60))

        for i, (param_name, _) in enumerate(parameters):
            param_text = prompt_font.render(f"{param_name}", True, WHITE)
            screen.blit(param_text, (WIDTH // 2 - param_text.get_width() // 2, start_y + i * spacing))
            input_value = param_values[i] + ("|" if i == active_param else "")
            input_text = info_font.render(input_value, True, WHITE)
            input_rect = input_boxes[i]
            pygame.draw.rect(screen, CYAN if i == active_param else WHITE, input_rect, 3)
            screen.blit(input_text, (input_rect.x + 10, input_rect.y + (box_height - input_text.get_height()) // 2))
        
        pygame.draw.rect(screen, WHITE if active_param != 2 else CYAN, checkbox_rect, 2)
        if isi_varies:
            pygame.draw.line(screen, WHITE, (checkbox_rect.x + 4, checkbox_rect.y + 10), 
                            (checkbox_rect.x + 10, checkbox_rect.y + 16), 2)
            pygame.draw.line(screen, WHITE, (checkbox_rect.x + 10, checkbox_rect.y + 16), 
                            (checkbox_rect.x + 16, checkbox_rect.y + 4), 2)
        varies_text = info_font.render("Varies?", True, WHITE)
        screen.blit(varies_text, (checkbox_rect.x + 25, checkbox_rect.y - 5))

        stim_type_text = prompt_font.render("Stimuli Type:", True, WHITE)
        screen.blit(stim_type_text, (WIDTH // 2 - stim_type_text.get_width() // 2, start_y + 4 * spacing))
        modes = ["Both", "Audio", "Visual"]
        for i, rect in enumerate(radio_rects):
            pygame.draw.circle(screen, WHITE, rect.center, 10, 2)
            if stim_type == ["both", "audio", "visual"][i]:
                pygame.draw.circle(screen, CYAN, rect.center, 6)
            mode_text = info_font.render(modes[i], True, WHITE)
            screen.blit(mode_text, (rect.x + 25, rect.y - 5))

        instruction_text = info_font.render("Press Enter to continue", True, WHITE)
        screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, start_y + 5 * spacing + 20))
        pygame.display.flip()

    # Convert parameters
    TOTAL_TRIALS = int(param_values[0])
    STIM_DURATION = int(param_values[1])
    BASE_ISI = int(param_values[2])
    NUM_BLOCKS = int(param_values[3])
    ISI_VARIES = isi_varies
    STIM_TYPE = stim_type

    # Generate stimulus sounds
    standard_sound = generate_tone(500, STIM_DURATION)
    target_sound = generate_tone(1000, STIM_DURATION)

    print("Testing correct chime...")
    correct_chime.play()
    pygame.time.wait(250)

    # Instruction screen
    screen.fill(DARK_GRAY)
    pygame.draw.rect(screen, BLACK, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2), 5)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4 + 20))
    if STIM_TYPE == "both":
        instruction_text1 = prompt_font.render(f"{user_name}, press the spacebar only", True, WHITE)
        instruction_text2 = prompt_font.render("when the green triangle or high tone occurs", True, WHITE)
    elif STIM_TYPE == "audio":
        instruction_text1 = prompt_font.render(f"{user_name}, press the spacebar only", True, WHITE)
        instruction_text2 = prompt_font.render("when you hear the high tone", True, WHITE)
    else:  # visual
        instruction_text1 = prompt_font.render(f"{user_name}, press the spacebar only", True, WHITE)
        instruction_text2 = prompt_font.render("when the green triangle is displayed", True, WHITE)
    instruction_text3 = info_font.render("Press any key to start", True, CYAN)
    screen.blit(instruction_text1, (WIDTH // 2 - instruction_text1.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(instruction_text2, (WIDTH // 2 - instruction_text2.get_width() // 2, HEIGHT // 2))
    screen.blit(instruction_text3, (WIDTH // 2 - instruction_text3.get_width() // 2, HEIGHT // 2 + 60))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN:
                waiting = False

    # Countdown
    for count in ["3", "2", "1", "GO!"]:
        screen.fill(DARK_GRAY)
        pygame.draw.rect(screen, BLACK, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2), 5)
        count_text = countdown_font.render(count, True, CYAN)
        screen.blit(count_text, (WIDTH // 2 - count_text.get_width() // 2, HEIGHT // 2 - count_text.get_height() // 2))
        pygame.display.flip()
        pygame.time.wait(1000)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    # Main experiment loop
    all_logs = []

    for block_num in range(1, NUM_BLOCKS + 1):
        num_standards = int(TOTAL_TRIALS * (1 - TARGET_PROB))
        num_targets = int(TOTAL_TRIALS * TARGET_PROB)
        trials = ['standard'] * (num_standards - 1) + ['target'] * num_targets
        random.shuffle(trials)
        trials.insert(0, 'standard')  # Force first trial to be standard
        
        trial_idx = 0
        while trial_idx < TOTAL_TRIALS:
            screen.fill(BLACK)
            stim_type = trials[trial_idx]
            
            # Adjust stimulus presentation and square color
            if stim_type == 'standard':
                if STIM_TYPE in ["both", "visual"]:
                    pygame.draw.circle(screen, RED, (WIDTH // 2, HEIGHT // 2), 100)
                if STIM_TYPE in ["both", "audio"]:
                    standard_sound.play()
                pygame.draw.rect(screen, BLACK, (WIDTH - SQUARE_SIZE - 10, HEIGHT - SQUARE_SIZE - 10, SQUARE_SIZE, SQUARE_SIZE))  # Black for non-target
            else:  # target
                if STIM_TYPE in ["both", "visual"]:
                    pygame.draw.polygon(screen, GREEN, 
                                       [(WIDTH // 2, HEIGHT // 2 - 100), 
                                        (WIDTH // 2 - 100, HEIGHT // 2 + 100), 
                                        (WIDTH // 2 + 100, HEIGHT // 2 + 100)])
                if STIM_TYPE in ["both", "audio"]:
                    target_sound.play()
                pygame.draw.rect(screen, WHITE, (WIDTH - SQUARE_SIZE - 10, HEIGHT - SQUARE_SIZE - 10, SQUARE_SIZE, SQUARE_SIZE))  # White for target
            
            pygame.display.flip()
            stim_start_time = time.time()
            response_made = False
            
            end_stim_time = stim_start_time + STIM_DURATION / 1000
            while time.time() < end_stim_time:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.VIDEORESIZE:
                        WIDTH, HEIGHT = event.w, event.h
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        rt = round((time.time() - stim_start_time) * 1000, 2)
                        if stim_type == 'target' and not response_made:
                            all_logs.append({'block': block_num, 'trial': trial_idx + 1, 'reaction_time': rt, 'correct': 1})
                            print(f"Block {block_num}, Trial {trial_idx + 1}, RT: {rt} ms, Correct")
                            correct_chime.play()
                            response_made = True
                        else:
                            all_logs.append({'block': block_num, 'trial': trial_idx + 1, 'reaction_time': rt, 'correct': 0})
                            print(f"Block {block_num}, Trial {trial_idx + 1}, RT: {rt} ms, Incorrect")
                            incorrect_chime.play()
            
            screen.fill(BLACK)
            pygame.display.flip()
            
            isi = BASE_ISI if not ISI_VARIES else random.uniform(BASE_ISI - 500, BASE_ISI + 500)
            isi = max(50, isi)  # Minimum 50 ms
            end_isi_time = stim_start_time + (STIM_DURATION + isi) / 1000
            while time.time() < end_isi_time:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.VIDEORESIZE:
                        WIDTH, HEIGHT = event.w, event.h
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        rt = round((time.time() - stim_start_time) * 1000, 2)
                        if stim_type == 'target' and not response_made:
                            all_logs.append({'block': block_num, 'trial': trial_idx + 1, 'reaction_time': rt, 'correct': 1})
                            print(f"Block {block_num}, Trial {trial_idx + 1}, RT: {rt} ms, Correct")
                            correct_chime.play()
                            response_made = True
                        else:
                            all_logs.append({'block': block_num, 'trial': trial_idx + 1, 'reaction_time': rt, 'correct': 0})
                            print(f"Block {block_num}, Trial {trial_idx + 1}, RT: {rt} ms, Incorrect")
                            incorrect_chime.play()
            
            trial_idx += 1

        if block_num < NUM_BLOCKS:
            screen.fill(DARK_GRAY)
            pygame.draw.rect(screen, BLACK, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2), 5)
            break_text1 = prompt_font.render(f"Block {block_num} finished", True, WHITE)
            break_text2 = prompt_font.render(f"Ready for block {block_num + 1}?", True, WHITE)
            break_text3 = info_font.render("Press any key when ready", True, CYAN)
            screen.blit(break_text1, (WIDTH // 2 - break_text1.get_width() // 2, HEIGHT // 2 - 70))
            screen.blit(break_text2, (WIDTH // 2 - break_text2.get_width() // 2, HEIGHT // 2 - 20))
            screen.blit(break_text3, (WIDTH // 2 - break_text3.get_width() // 2, HEIGHT // 2 + 40))
            pygame.display.flip()

            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.VIDEORESIZE:
                        WIDTH, HEIGHT = event.w, event.h
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    if event.type == pygame.KEYDOWN:
                        waiting = False

    # Save logs
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    filename = f"oddball_log_{user_name}_{timestamp}.csv"
    print(f"Final log before saving: {all_logs}")
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['block', 'trial', 'reaction_time', 'correct'])
        writer.writeheader()
        writer.writerows(all_logs)

    # End screen
    screen.fill(DARK_GRAY)
    pygame.draw.rect(screen, BLACK, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2), 5)
    end_text = prompt_font.render("Thank you for participating!", True, WHITE)
    restart_text = info_font.render("Press X to go to the main menu", True, CYAN)
    screen.blit(end_text, (WIDTH // 2 - end_text.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                waiting = False

# Cleanup
pygame.quit()