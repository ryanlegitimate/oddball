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
STIM_DURATION = 500
STANDARD_PULSE = 128  # Duration for non-target square pulse in ms
TARGET_PULSE = 512    # Duration for target square pulse in ms
ISI = 1000 
NUM_BLOCKS = 1
TARGET_PROB = 0.2
ISI_VARIES = False
STIM_TYPE = "both"
FIXATION_CROSS = True  # Default to True (checked)
FIXATION_DURATION = 750  # Default to 750ms

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
        ("Number of blocks", str(NUM_BLOCKS)),
        ("Fixation duration (ms)", str(FIXATION_DURATION)),
        ("Diode pulse length (target, ms)", str(TARGET_PULSE)),  # Added
        ("Diode pulse length (non-target, ms)", str(STANDARD_PULSE))  # Added
    ]
    param_values = [pair[1] for pair in parameters]
    active_param = 0
    isi_varies = ISI_VARIES
    stim_type = STIM_TYPE
    fixation_cross = FIXATION_CROSS  # Default to True
    entering_params = True

    input_boxes = []
    box_width, box_height = 200, 40
    start_y = 150
    spacing = 70
    for i in range(len(parameters)):
        y_pos = start_y + i * spacing
        input_boxes.append(pygame.Rect(WIDTH // 2 - box_width // 2, y_pos + 30, box_width, box_height))
    
    checkbox_rect_isi = pygame.Rect(WIDTH // 2 + box_width // 2 + 10, start_y + 2 * spacing + 30, 20, 20)
    checkbox_rect_fixation = pygame.Rect(WIDTH // 2 + box_width // 2 + 10, start_y + 4 * spacing + 30, 20, 20)  # New checkbox for fixation
    radio_rects = [
        pygame.Rect(WIDTH // 2 - 150, start_y + 7 * spacing + 30, 20, 20),  # Both
        pygame.Rect(WIDTH // 2 - 50, start_y + 7 * spacing + 30, 20, 20),   # Audio
        pygame.Rect(WIDTH // 2 + 50, start_y + 7 * spacing + 30, 20, 20)    # Visual
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
                checkbox_rect_isi = pygame.Rect(WIDTH // 2 + box_width // 2 + 10, start_y + 2 * spacing + 30, 20, 20)
                checkbox_rect_fixation = pygame.Rect(WIDTH // 2 + box_width // 2 + 10, start_y + 4 * spacing + 30, 20, 20)
                radio_rects = [
                    pygame.Rect(WIDTH // 2 - 150, start_y + 7 * spacing + 30, 20, 20),
                    pygame.Rect(WIDTH // 2 - 50, start_y + 7 * spacing + 30, 20, 20),
                    pygame.Rect(WIDTH // 2 + 50, start_y + 7 * spacing + 30, 20, 20)
                ]
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, box in enumerate(input_boxes):
                    if box.collidepoint(event.pos):
                        active_param = i
                if checkbox_rect_isi.collidepoint(event.pos):
                    isi_varies = not isi_varies
                if checkbox_rect_fixation.collidepoint(event.pos):
                    fixation_cross = not fixation_cross
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
        
        # ISI variation checkbox
        pygame.draw.rect(screen, WHITE if active_param != 2 else CYAN, checkbox_rect_isi, 2)
        if isi_varies:
            pygame.draw.line(screen, WHITE, (checkbox_rect_isi.x + 4, checkbox_rect_isi.y + 10), 
                            (checkbox_rect_isi.x + 10, checkbox_rect_isi.y + 16), 2)
            pygame.draw.line(screen, WHITE, (checkbox_rect_isi.x + 10, checkbox_rect_isi.y + 16), 
                            (checkbox_rect_isi.x + 16, checkbox_rect_isi.y + 4), 2)
        varies_text = info_font.render("500ms variation", True, WHITE)
        screen.blit(varies_text, (checkbox_rect_isi.x + 25, checkbox_rect_isi.y - 5))

        # Fixation cross checkbox
        pygame.draw.rect(screen, WHITE if active_param != 4 else CYAN, checkbox_rect_fixation, 2)
        if fixation_cross:
            pygame.draw.line(screen, WHITE, (checkbox_rect_fixation.x + 4, checkbox_rect_fixation.y + 10), 
                            (checkbox_rect_fixation.x + 10, checkbox_rect_fixation.y + 16), 2)
            pygame.draw.line(screen, WHITE, (checkbox_rect_fixation.x + 10, checkbox_rect_fixation.y + 16), 
                            (checkbox_rect_fixation.x + 16, checkbox_rect_fixation.y + 4), 2)
        fixation_text = info_font.render("Fixation cross?", True, WHITE)
        screen.blit(fixation_text, (checkbox_rect_fixation.x + 25, checkbox_rect_fixation.y - 5))

        # Stimulus type radio buttons
        stim_type_text = prompt_font.render("Stimuli Type:", True, WHITE)
        screen.blit(stim_type_text, (WIDTH // 2 - stim_type_text.get_width() // 2, start_y + 7 * spacing))
        modes = ["Both", "Audio", "Visual"]
        for i, rect in enumerate(radio_rects):
            pygame.draw.circle(screen, WHITE, rect.center, 10, 2)
            if stim_type == ["both", "audio", "visual"][i]:
                pygame.draw.circle(screen, CYAN, rect.center, 6)
            mode_text = info_font.render(modes[i], True, WHITE)
            screen.blit(mode_text, (rect.x + 25, rect.y - 5))

        instruction_text = info_font.render("Press Enter to continue", True, WHITE)
        screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, start_y + 8 * spacing + 20))
        pygame.display.flip()

    # Convert parameters
    TOTAL_TRIALS = int(param_values[0])
    STIM_DURATION = int(param_values[1])
    BASE_ISI = int(param_values[2])
    NUM_BLOCKS = int(param_values[3])
    FIXATION_DURATION = int(param_values[4]) if fixation_cross else 0  # Use 0 if fixation is off
    TARGET_PULSE = int(param_values[5])  # Added
    STANDARD_PULSE = int(param_values[6])  # Added
    ISI_VARIES = isi_varies
    STIM_TYPE = stim_type
    FIXATION_CROSS = fixation_cross

    # Generate stimulus sounds
    standard_sound = generate_tone(1000, STIM_DURATION)
    target_sound = generate_tone(1500, STIM_DURATION)

    print("Testing correct chime...")
    correct_chime.play()
    pygame.time.wait(250)

    # Instruction screen
    screen.fill(DARK_GRAY)
    pygame.draw.rect(screen, BLACK, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2), 5)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4 + 20))
    if STIM_TYPE == "both":
        instruction_text1 = prompt_font.render(f"{user_name}, press the spacebar", True, WHITE)
        instruction_text2 = prompt_font.render("when the green triangle or high tone occurs", True, WHITE)
    elif STIM_TYPE == "audio":
        instruction_text1 = prompt_font.render(f"{user_name}, press the spacebar", True, WHITE)
        instruction_text2 = prompt_font.render("when you hear the high tone", True, WHITE)
    else:  # visual
        instruction_text1 = prompt_font.render(f"{user_name}, press the spacebar", True, WHITE)
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
    experiment_running = True

    for block_num in range(1, NUM_BLOCKS + 1):
        if not experiment_running:
            break

        num_standards = int(TOTAL_TRIALS * (1 - TARGET_PROB))
        num_targets = int(TOTAL_TRIALS * TARGET_PROB)
        trials = ['standard'] * (num_standards - 1) + ['target'] * num_targets
        random.shuffle(trials)
        trials.insert(0, 'standard')  # Force first trial to be standard
        
        trial_idx = 0
        while trial_idx < TOTAL_TRIALS and experiment_running:
            # Display fixation cross if enabled
            if FIXATION_CROSS:
                screen.fill(BLACK)
                pygame.draw.line(screen, WHITE, (WIDTH // 2 - 20, HEIGHT // 2), (WIDTH // 2 + 20, HEIGHT // 2), 4)  # Horizontal
                pygame.draw.line(screen, WHITE, (WIDTH // 2, HEIGHT // 2 - 20), (WIDTH // 2, HEIGHT // 2 + 20), 4)  # Vertical
                pygame.display.flip()
                fixation_start_time = time.time()
                while time.time() < fixation_start_time + FIXATION_DURATION / 1000:  # Convert ms to seconds
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            exit()
                        if event.type == pygame.VIDEORESIZE:
                            WIDTH, HEIGHT = event.w, event.h
                            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

            # Now present the stimulus
            screen.fill(BLACK)  # Changed to BLACK background
            stim_type = trials[trial_idx]
            
            # Set pulse duration based on stimulus type
            pulse_duration = STANDARD_PULSE if stim_type == 'standard' else TARGET_PULSE
            
            # Draw main stimulus
            if stim_type == 'standard':
                if STIM_TYPE in ["both", "visual"]:
                    pygame.draw.circle(screen, RED, (WIDTH // 2, HEIGHT // 2), 100)
                if STIM_TYPE in ["both", "audio"]:
                    standard_sound.play()
            else:  # target
                if STIM_TYPE in ["both", "visual"]:
                    pygame.draw.polygon(screen, GREEN, 
                                       [(WIDTH // 2, HEIGHT // 2 - 100), 
                                        (WIDTH // 2 - 100, HEIGHT // 2 + 100), 
                                        (WIDTH // 2 + 100, HEIGHT // 2 + 100)])
                if STIM_TYPE in ["both", "audio"]:
                    target_sound.play()
            
            # Draw initial white square for both trial types
            pygame.draw.rect(screen, WHITE, (WIDTH - SQUARE_SIZE - 10, HEIGHT - SQUARE_SIZE - 10, SQUARE_SIZE, SQUARE_SIZE))
            
            pygame.display.flip()
            stim_start_time = time.time()
            response_made = False
            square_active = True
            
            pulse_end_time = stim_start_time + pulse_duration / 1000
            stim_end_time = stim_start_time + STIM_DURATION / 1000
            
            # Run loop until the longer of STIM_DURATION and pulse_duration
            end_time = max(stim_end_time, pulse_end_time)
            while time.time() < end_time:
                current_time = time.time()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.VIDEORESIZE:
                        WIDTH, HEIGHT = event.w, event.h
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            # Pause and show quit prompt
                            screen.fill(BLACK)
                            quit_text = prompt_font.render("Quit? (Y/N)", True, WHITE)
                            screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 - quit_text.get_height() // 2))
                            pygame.display.flip()
                            
                            waiting_for_quit_response = True
                            while waiting_for_quit_response:
                                for quit_event in pygame.event.get():
                                    if quit_event.type == pygame.QUIT:
                                        pygame.quit()
                                        exit()
                                    if quit_event.type == pygame.KEYDOWN:
                                        if quit_event.key == pygame.K_y:
                                            experiment_running = False  # Break out of experiment loop
                                            waiting_for_quit_response = False
                                            break  # Return to main menu
                                        elif quit_event.key == pygame.K_n:
                                            waiting_for_quit_response = False
                                            # Redraw the current stimulus
                                            screen.fill(BLACK)
                                            if current_time < stim_end_time and STIM_TYPE in ["both", "visual"]:
                                                if stim_type == 'standard':
                                                    pygame.draw.circle(screen, RED, (WIDTH // 2, HEIGHT // 2), 100)
                                                elif stim_type == 'target':
                                                    pygame.draw.polygon(screen, GREEN, 
                                                                       [(WIDTH // 2, HEIGHT // 2 - 100), 
                                                                        (WIDTH // 2 - 100, HEIGHT // 2 + 100), 
                                                                        (WIDTH // 2 + 100, HEIGHT // 2 + 100)])
                                            pygame.draw.rect(screen, WHITE if square_active else BLACK, 
                                                            (WIDTH - SQUARE_SIZE - 10, HEIGHT - SQUARE_SIZE - 10, SQUARE_SIZE, SQUARE_SIZE))
                                            pygame.display.flip()
                                            # Adjust timing to account for pause
                                            pause_duration = time.time() - current_time
                                            stim_end_time += pause_duration
                                            pulse_end_time += pause_duration
                                            end_time = max(stim_end_time, pulse_end_time)
                                            break
                        
                        elif event.key == pygame.K_SPACE:
                            rt = round((current_time - stim_start_time) * 1000, 2)
                            if stim_type == 'target' and not response_made:
                                all_logs.append({'block': block_num, 'trial': trial_idx + 1, 'stim_type': stim_type, 'reaction_time': rt, 'correct': 1, 'target': 1, 'reported_targets': None})
                                print(f"Block {block_num}, Trial {trial_idx + 1}, Stim: {stim_type}, RT: {rt} ms, Correct")
                                correct_chime.play()
                                response_made = True
                            else:
                                all_logs.append({'block': block_num, 'trial': trial_idx + 1, 'stim_type': stim_type, 'reaction_time': rt, 'correct': 0, 'target': 0 if stim_type == 'standard' else 1, 'reported_targets': None})
                                print(f"Block {block_num}, Trial {trial_idx + 1}, Stim: {stim_type}, RT: {rt} ms, Incorrect")
                                incorrect_chime.play()
                
                # Update square to black after pulse duration
                if current_time >= pulse_end_time and square_active:
                    screen.fill(BLACK)  # Changed to BLACK background
                    if current_time < stim_end_time and STIM_TYPE in ["both", "visual"]:
                        if stim_type == 'standard':
                            pygame.draw.circle(screen, RED, (WIDTH // 2, HEIGHT // 2), 100)
                        elif stim_type == 'target':
                            pygame.draw.polygon(screen, GREEN, 
                                              [(WIDTH // 2, HEIGHT // 2 - 100), 
                                               (WIDTH // 2 - 100, HEIGHT // 2 + 100), 
                                               (WIDTH // 2 + 100, HEIGHT // 2 + 100)])
                    pygame.draw.rect(screen, BLACK, (WIDTH - SQUARE_SIZE - 10, HEIGHT - SQUARE_SIZE - 10, SQUARE_SIZE, SQUARE_SIZE))
                    pygame.display.flip()
                    square_active = False
                
                # Clear stimulus if STIM_DURATION ends but pulse_duration continues
                if current_time >= stim_end_time and current_time < pulse_end_time and STIM_TYPE in ["both", "visual"]:
                    screen.fill(BLACK)
                    pygame.draw.rect(screen, WHITE, (WIDTH - SQUARE_SIZE - 10, HEIGHT - SQUARE_SIZE - 10, SQUARE_SIZE, SQUARE_SIZE))
                    pygame.display.flip()
            
            screen.fill(BLACK)  # Changed to BLACK background
            pygame.display.flip()
            
            isi = BASE_ISI if not ISI_VARIES else random.uniform(BASE_ISI - 500, BASE_ISI + 500)
            isi = max(50, isi)  # Minimum 50 ms
            end_isi_time = stim_start_time + (max(STIM_DURATION, pulse_duration) + isi) / 1000  # Start ISI after the longer duration
            while time.time() < end_isi_time and experiment_running:
                current_time = time.time()  # Capture time before potential pause
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.VIDEORESIZE:
                        WIDTH, HEIGHT = event.w, event.h
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            # Pause and show quit prompt during ISI
                            screen.fill(BLACK)
                            quit_text = prompt_font.render("Quit? (Y/N)", True, WHITE)
                            screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 - quit_text.get_height() // 2))
                            pygame.display.flip()
                            
                            waiting_for_quit_response = True
                            while waiting_for_quit_response:
                                for quit_event in pygame.event.get():
                                    if quit_event.type == pygame.QUIT:
                                        pygame.quit()
                                        exit()
                                    if quit_event.type == pygame.KEYDOWN:
                                        if quit_event.key == pygame.K_y:
                                            experiment_running = False  # Break out of experiment loop
                                            waiting_for_quit_response = False
                                            break  # Return to main menu
                                        elif quit_event.key == pygame.K_n:
                                            waiting_for_quit_response = False
                                            screen.fill(BLACK)
                                            pygame.display.flip()
                                            # Adjust ISI timing
                                            pause_duration = time.time() - current_time
                                            end_isi_time += pause_duration
                                            break
                        elif event.key == pygame.K_SPACE and not response_made:
                            rt = round((time.time() - stim_start_time) * 1000, 2)
                            if stim_type == 'target':
                                all_logs.append({'block': block_num, 'trial': trial_idx + 1, 'stim_type': stim_type, 'reaction_time': rt, 'correct': 1, 'target': 1, 'reported_targets': None})
                                print(f"Block {block_num}, Trial {trial_idx + 1}, Stim: {stim_type}, RT: {rt} ms, Correct")
                                correct_chime.play()
                                response_made = True
                            else:
                                all_logs.append({'block': block_num, 'trial': trial_idx + 1, 'stim_type': stim_type, 'reaction_time': rt, 'correct': 0, 'target': 0, 'reported_targets': None})
                                print(f"Block {block_num}, Trial {trial_idx + 1}, Stim: {stim_type}, RT: {rt} ms, Incorrect")
                                incorrect_chime.play()
            
            # Log the trial even if no response was made
            if not response_made and experiment_running:
                all_logs.append({
                    'block': block_num,
                    'trial': trial_idx + 1,
                    'stim_type': stim_type,
                    'reaction_time': None,
                    'correct': 0 if stim_type == 'target' else 1,
                    'target': 1 if stim_type == 'target' else 0,
                    'reported_targets': None
                })
                print(f"Block {block_num}, Trial {trial_idx + 1}, Stim: {stim_type}, No response")
            
            trial_idx += 1

        if experiment_running:
            # Ask participant how many targets they saw at the end of each block
            target_count = ""
            getting_target_count = True
            while getting_target_count:
                screen.fill(DARK_GRAY)
                pygame.draw.rect(screen, BLACK, (WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2), 5)
                prompt_text1 = prompt_font.render(f"Block {block_num} finished", True, WHITE)
                prompt_text2 = prompt_font.render("How many targets did you see?", True, WHITE)
                prompt_text3 = info_font.render(target_count + "|", True, WHITE)
                prompt_text4 = info_font.render("Press Enter to continue", True, CYAN)
                screen.blit(prompt_text1, (WIDTH // 2 - prompt_text1.get_width() // 2, HEIGHT // 2 - 80))
                screen.blit(prompt_text2, (WIDTH // 2 - prompt_text2.get_width() // 2, HEIGHT // 2 - 30))
                screen.blit(prompt_text3, (WIDTH // 2 - prompt_text3.get_width() // 2, HEIGHT // 2 + 20))
                screen.blit(prompt_text4, (WIDTH // 2 - prompt_text4.get_width() // 2, HEIGHT // 2 + 70))
                pygame.display.flip()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    if event.type == pygame.VIDEORESIZE:
                        WIDTH, HEIGHT = event.w, event.h
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN and target_count:
                            getting_target_count = False
                            # Store the participant's count in the logs
                            all_logs.append({
                                'block': block_num,
                                'trial': 'summary',
                                'stim_type': 'target_count',
                                'reaction_time': None,
                                'correct': None,
                                'target': None,
                                'reported_targets': int(target_count)
                            })
                        elif event.key == pygame.K_BACKSPACE:
                            target_count = target_count[:-1]
                        elif event.unicode.isdigit():
                            target_count += event.unicode

        if block_num < NUM_BLOCKS and experiment_running:
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

    if experiment_running:
        # Save logs
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        filename = f"oddball_log_{user_name}_{timestamp}.csv"
        print(f"Final log before saving: {all_logs}")
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['block', 'trial', 'stim_type', 'reaction_time', 'correct', 'target', 'reported_targets'])
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