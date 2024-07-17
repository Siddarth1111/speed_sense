import os
import cv2
from ultralytics import YOLO
from ultralytics.solutions.speed_estimation import SpeedEstimator
import tkinter
from tkinter import *
from tkinter import filedialog, messagebox
import sendemail

def detect_and_save_vehicle_image(im0, bbox, output_folder, speed):
    x1, y1, x2, y2 = map(int, bbox)
    vehicle_image = im0[y1:y2, x1:x2]

    font = cv2.FONT_HERSHEY_SIMPLEX
    speed_text = str(round(speed, 2)) + " km/h"
    cv2.putText(vehicle_image,
                speed_text,
                (10, 30),
                font, 1,
                (0, 255, 255),
                2,
                cv2.LINE_4)

    imshow_screenshot_path = os.path.join(output_folder, f"vehicle_speed_{round(speed, 2)}kmph.png")
    cv2.imwrite(imshow_screenshot_path, vehicle_image)
    print(f"Vehicle image saved as {imshow_screenshot_path}")

def box_intersects_line(box, line):
    box_x1, box_y1, box_x2, box_y2 = map(int, box)
    line_x1, line_y1, line_x2, line_y2 = line
    if line_y1 == line_y2:  # Horizontal line
        return box_y1 <= line_y1 <= box_y2
    return False

def calculate_estimate_and_display_speed(im0, model, speed_obj, video_writer, output_folder, user_speed):
    display_width = 1920
    display_height = 1080
    im0_resized = cv2.resize(im0, (display_width, display_height))

    # Perform object detection and tracking
    car_class_index = [1, 2, 3, 4, 5, 6, 7, 8]
    results = model.track(im0_resized, classes=car_class_index, persist=True, show=False)

    # Estimate and display speed
    im0_with_speed = speed_obj.estimate_speed(im0_resized, results)

    # Calculate and print speed for each new track
    new_tracks = set(speed_obj.dist_data.keys()) - speed_obj.printed_tracks
    for track_id in new_tracks:
        speed = speed_obj.dist_data[track_id]
        if speed > user_speed:
            print(f"Track {track_id}: Speed = {speed} km/h")
            speed_obj.printed_tracks.add(track_id)

            # Get bounding box for the vehicle
            bbox = None
            for result in results:
                if hasattr(result, 'boxes'):
                    for box, tid in zip(result.boxes.xyxy, result.boxes.id):
                        if tid == track_id:
                            bbox = box
                            break
                if bbox is not None:
                    break

            if bbox is not None and box_intersects_line(bbox, (0, 540, 1920, 540)):
                detect_and_save_vehicle_image(im0_resized, bbox, output_folder, speed)

    # Write frame to video
    video_writer.write(im0_with_speed)

    return im0_with_speed

def process_video(video_path, user_speed):
    model = YOLO("yolov8n.pt")
    names = model.model.names
    final_names = {k: v for k, v in names.items() if k in range(1, 9)}
    print(final_names)

    cap = cv2.VideoCapture(video_path)
    assert cap.isOpened(), "Error reading video file"
    fps = cap.get(cv2.CAP_PROP_FPS)
    print("FPS OF VIDEO IS: ", fps)

    output_folder = "screenshots"
    os.makedirs(output_folder, exist_ok=True)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_writer = cv2.VideoWriter("backup_footage.avi",
                                   cv2.VideoWriter_fourcc(*'mp4v'),
                                   fps,
                                   (width, height))

    line_pts = [(0, 540), (1920, 540)]

    speed_obj = SpeedEstimator(names=final_names, reg_pts=line_pts, view_img=False)
    speed_obj.printed_tracks = set()

    while cap.isOpened():
        success, im0 = cap.read()
        if not success:
            break
        im0_with_speed = calculate_estimate_and_display_speed(im0, model, speed_obj, video_writer, output_folder, user_speed)

        # Display the frame with speed information
        cv2.imshow('Speed Sense', im0_with_speed)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("User pressed 'q'. Exiting...")
            break

    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()

    messagebox.showinfo("Processing Complete", "The video processing has been successfully completed.")
    sendemail.send_email()

def get_speed():
    try:
        user_speed = int(speed.get())
        if user_speed < 0 or user_speed > 250:
            raise ValueError("Invalid speed limit")
    except ValueError as e:
        messagebox.showerror("Invalid Entry", "Please enter a valid speed limit.")
        speed.delete(0, END)
        return

    video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
    if video_path:
        window.destroy()
        process_video(video_path, user_speed)
    else:
        messagebox.showwarning("No File Selected", "Please select a video file to proceed.")
        return

window = tkinter.Tk()
window.geometry('400x300')
window.title('Speed Sense')
window.configure(bg='black')

frame = Frame(window, bg='black')
frame.pack(expand=True, padx=20, pady=20)
title = Label(frame, text='Speed Sense', font=('Helvetica', 24), bg='black', fg='white')
title.pack(pady=10)
w = Label(frame, text='Enter the speed limit in Km/h:', font=('Helvetica', 14), bg='black', fg='white')
w.pack(pady=10)

speed = Entry(frame, font=('Helvetica', 12), bd=2, relief='raised')
speed.pack(pady=10)

button = tkinter.Button(frame, text="OK", command=get_speed, font=('Helvetica', 12), bg='#4CAF50', fg='white', bd=2, relief='raised')
button.pack(pady=10)

window.mainloop()

