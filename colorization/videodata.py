import cv2
import os
import numpy
from moviepy.editor import AudioFileClip
from moviepy.editor import VideoFileClip

SUCCESS = 0
FAILED = 1
fps = 0


def video2frames(video_input_path, image_output_folder_path):
    """This function is used to convert video into images.
     Args:
        video_input_path: filename of the video.
        image_output_folder_path: Output folder path containing images
     Returns:
        1 on fail.
        0 on success.
     """
    video = cv2.VideoCapture(video_input_path)
    type = os.path.splitext(video_input_path)[-1]
    if (video.isOpened() is False) or (not (type == '.mp4')):
        print("Error opening video")
        return FAILED
    global FPS
    FPS = int(video.get(cv2.CAP_PROP_FPS))
    currentFrame = 0
    while (video.isOpened()):
        ret, frame = video.read()
        if ret is True:
            folder_name = os.path.join(image_output_folder_path,
                                       str(currentFrame) + '.png')
            cv2.imwrite(folder_name, frame)
            currentFrame += 1
        else:
            break
    video.release()
    return SUCCESS


def frames2video(image_input_folder_path, video_output_path):
    """This function is used to convert images into a video.
    Args:
        image_input_folder_path: path to the split images.
        video_output_path: path to the merged video
    Returns:
        0 for SUCCESS.
        1 for FAILED.

    """
    mat = cv2.imread(os.path.join(image_input_folder_path + '/0.png'),
                     cv2.IMREAD_COLOR)
    if numpy.any(mat) is None:
        return FAILED
    size = mat.shape[:2]
    fourcc = cv2.VideoWriter_fourcc('D', 'I', 'V', 'X')
    video = cv2.VideoWriter(video_output_path,
                            fourcc, FPS, (size[1], size[0]))
    files = os.listdir(image_input_folder_path)
    length = len(files)
    for i in range(0, length):
        index = str(i)
        item = image_input_folder_path + '/' + index + '.png'
        img = cv2.imread(item)
        video.write(img)
    video.release()
    return SUCCESS


def split_audio_from_video(video_input_path, audio_output_path):
    """This function is used to extract voice from a video.
    Args:
        video_input_path: path of the origin video
        audio_output_path: path to the voice file
    Returns: int
        on success this function returns 0
        on failure this function returns 1
    """
    if not os.path.isfile(video_input_path):
        print("invalid video path")
        return FAILED
    my_audio_clip = AudioFileClip(video_input_path)
    my_audio_clip.write_audiofile(audio_output_path)
    if not os.path.isfile(audio_output_path):
        print("invalid output path")
        return FAILED
    return SUCCESS


def merge_audio_and_video(video_input_path, audio_input_path, video_output_path):
    """This function is used to mge voice with a video merged from images.
    Args:
        video_input_path: path of the origin video
        audio_input_path: path of the voice file
        video_output_path: path to the result video
    Returns: int
        on success this function returns 0
        on failure this function returns 1
    """
    if not os.path.isfile(video_input_path):
        print("invalid video path")
        return FAILED
    if not os.path.isfile(audio_input_path):
        print("invalid audio path")
        return FAILED
    my_video_clip = VideoFileClip(video_input_path)
    my_audio_clip = AudioFileClip(audio_input_path)
    video = my_video_clip.set_audio(my_audio_clip)
    video.write_videofile(video_output_path, codec='mpeg4')
    if not os.path.isfile(video_output_path):
        print("invalid output path")
        return FAILED
    return SUCCESS
