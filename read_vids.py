import scenedetect
from scenedetect import open_video, SceneManager, ContentDetector
import time, datetime
import logging
import os
import cv2
import re
import json

# Send logs to stdout
scenedetect.platform.init_logger(log_level=logging.INFO, show_stdout=True)

class FrameReader():
    def __init__(self, dir):
        self.all_frames = {"guids": {}, "frames": []}
        self.guids = set()

        self.read_vids(dir)

    def read_vids(self, dir):
        for dir, subfolders, filenames in os.walk(dir):
            for filename in filenames:
                vid_path = os.path.join(dir, filename)
                guid = self.to_guid(filename)
                if vid_path.endswith(".mp4") and guid not in self.guids:
                    self.guids.add(guid)
                    self.update_guid(vid_path)
                    self.read_vid(vid_path)

    def update_guid(self, vid):
        cap = cv2.VideoCapture(vid)
        n_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        guid = self.to_guid(vid)
        self.all_frames["guids"][guid] = {"n_frames": n_frames}

    def to_guid(self, vid_path):
        try:
            guid = re.findall(r'cpb-aacip-[a-zA-Z0-9]*-[a-zA-Z0-9]*', vid_path)[0]
            guid = re.sub(r'^.*\/', '', guid)
        except:
            guid = os.path.splitext(os.path.basename(vid_path))[0]
        return guid

    def read_vid(self, vid_path):
        print("Reading", vid_path)
        read_start = time.time()

        guid = self.to_guid(vid_path)
        vid_basename = os.path.splitext(os.path.basename(vid_path))[0]
        # Run scene detection
        video = open_video(vid_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector())
        scene_manager.detect_scenes(video)
        scenes = scene_manager.get_scene_list()

        # Save images to image_outputs directory
        scenedetect.scene_manager.save_images(scenes, video, output_dir="image_outputs")

        # Save to dict
        for i, scene in enumerate(scenes):
            start, end = scene
            start, end = int(start.get_frames()), int(end.get_frames())
            for j, frame in enumerate((start+1, (end - round((end-start)/2)), end)):
                img_path = f"{vid_basename}-Scene-{i+1:03d}-{j+1:02d}.jpg"
                frame_dict = {"frame": frame, "guid": guid, "img_file": img_path}
                self.all_frames["frames"].append(frame_dict)
        
        read_end = time.time()
        print(f"Time elapsed: {datetime.timedelta(seconds=(read_end-read_start))}")


    def save_json(self):
        with open('scenes.json', 'w') as f:
            json.dump(self.all_frames, f, indent=4)

if __name__ == "__main__":
    frame_reader = FrameReader("test_vids")
    frame_reader.save_json()