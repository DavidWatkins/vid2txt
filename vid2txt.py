#! /usr/bin/env python
import argparse
from PIL import Image
import cv2
from jinja2 import Template
import subprocess
import IPython
import pexpect
import time
from subprocess import check_call, STDOUT, Popen, PIPE
from tempfile import NamedTemporaryFile
import os

def get_vidcap_info(vidcap):
    (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
    if int(major_ver) < 3:
        fps = vidcap.get(cv2.cv.CV_CAP_PROP_FPS)
        length = int(vidcap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
        print "Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps)
        print "Number of frames using video.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT) : {0}".format(length)
    else :
        fps = vidcap.get(cv2.CAP_PROP_FPS)
        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        print "Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps)
        print "Number of frames using video.get(cv2.CAP_PROP_FRAME_COUNT) : {0}".format(length)

    return fps, length

def frame2txt(frame, width=40, height=23):
    chs = "#MNHQ$OC?7>!:-;. "
    im = Image.fromarray(frame)
    im = im.resize((width, height))
    string = ''
    for h in range(height):
        for w in range(width):
            rgb = im.getpixel((w, h))
            string += chs[int(sum(rgb) / 3.0 / 256.0 * len(chs))]
        string += '\n'
    return string

def vid2txt_frames(video_file_name, max_frames, width=40, height=23, write_frames_to_file=False, write_txt_frames_to_file=False, out_dir=None):
    vidcap = cv2.VideoCapture(video_file_name)
    if not vidcap.isOpened():
        print("Could not open video file")
        exit()

    count = 0
    success = True

    fps, length = get_vidcap_info(vidcap)
    frame_interval = 1.0/fps * 1000

    if max_frames == 0:
        max_frames = length

    txt_frames = [None] * min(max_frames, length)
    print("Writing %d frames" % len(txt_frames))

    while success and (count < max_frames):
        success, frame = vidcap.read()
        if success:
            txt_frames[count] = frame2txt(frame, width, height)

            if write_frames_to_file:
                cv2.imwrite(out_dir + video_file_name + '.frame%d.jpg' % count, frame)
            if write_txt_frames_to_file:
                with open(out_dir + video_file_name + '.frame%d.txt' % count, 'w') as txt_file:
                    txt_file.write(str(txt_frames[count]))

            count += 1

    print("Read %d frames @ %d fps" % (count, fps))
    # print(txt_frames)
    return txt_frames, frame_interval

def read_txt_from_output(video_file_name, out_dir):
    vidcap = cv2.VideoCapture(video_file_name)
    if not vidcap.isOpened():
        print("Could not open video file")
        exit()
    fps, length = get_vidcap_info(vidcap)
    frame_interval = 1.0/fps * 1000
    txt_frames = [None] * length

    for i in range(length):
        try:
            with open(out_dir + video_file_name + '.frame%d.txt' % (i+1), 'r') as txt_file:
                txt_frames[i] = txt_file.read()
        except:
            pass

    return txt_frames, frame_interval

def write_txt_frames_to_html(out_filename, txt_frames, frame_interval):
    with open('template.jinja') as tpl_f:
        template = Template(tpl_f.read())
        html = template.render(strings=txt_frames, frame_interval=frame_interval)
    with open(out_filename, 'w') as out_f:
        out_f.write(html)
    print("Finished writing html file %s" % out_filename)

def write_txt_frames_to_mdb(mdb_filename, path_to_mdb_add, frame_interval, txt_frames, video_file_name):

    audio = Popen(["vlc", video_file_name[:-3] + "wav"])
    count = 0
    start_time = time.time()

    while count < len(txt_frames):
        print("Current frame: %d" % ((time.time() - start_time) * 1000 / frame_interval))
        count = int(((time.time() - start_time) * 1000 / frame_interval))
        frame = txt_frames[count]
        start = time.time()
        for line in frame.splitlines():
            
            with open('tmp.txt', 'w') as tmp:
                tmp.write(line[0:14] + "\n" + line[15:39] + "\n")

            os.system(path_to_mdb_add + " " + mdb_filename + " < tmp.txt > /dev/zero")
        end = time.time()

        print("Wrote frame %d in %fms (frame_interval %fms)" % (count, (end-start)*1000, frame_interval))

        if end-start > frame_interval:
            time.sleep(frame_interval/1000 - (end-start))

    audio.kill()

def extract_audio(video_file_name):
    audio_file_name = video_file_name[:-3] + "wav"
    command = "ffmpeg -i " + video_file_name + " -ab 160k -ac 2 -ar 44100 -vn " + audio_file_name
    subprocess.call(command, shell=True)
    return audio_file_name

def vid2txt(args):

    if args.convert:
        txt_frames, frame_interval = vid2txt_frames(args.filename, args.maxFrames, args.width, args.height, write_frames_to_file=False, write_txt_frames_to_file=True, out_dir=args.output)
    else:
        txt_frames, frame_interval = read_txt_from_output(args.filename, args.output)

    if args.html:
        write_txt_frames_to_html(args.html, txt_frames, frame_interval)
    if args.extractAudio:
        audio_file_name = extract_audio(args.filename)
    if args.mdba:
        write_txt_frames_to_mdb(args.mdbl, args.mdba, frame_interval, txt_frames, args.filename)
    # play_audio(audio_file_name)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('filename', help='Mp4 input file')
    parser.add_argument('-width', '--width', type=int, help='Width of the output txt video')
    parser.add_argument('-height', '--height', type=int, help='Height of the output txt video')
    parser.add_argument('-o', '--output', help='Name of the output directory')
    parser.add_argument('-html', '--html', help='Name of the html output file')
    parser.add_argument('-mdba', '--mdba', help='Name of the location of the mdb-add executable')
    parser.add_argument('-mdbl', '--mdbl', help='Path to the mdb file')
    parser.add_argument("-mf", '--maxFrames', type=int, help='Maximum frames to use from video')
    parser.add_argument("-ea", "--extractAudio",  action='store_true', help='Extract the audio from the video')
    parser.add_argument("-c", "--convert", action='store_true', help="Convert the video to txt")
    args = parser.parse_args()

    if not args.width:
        args.width = 40
    if not args.height:
        args.height = 23
    if not args.output:
        args.output = 'images/'

    if not args.maxFrames:
        args.maxFrames = 0

    if args.mdba and not args.mdbl or not args.mdba and args.mdbl:
        print("Cannot open mdb without corresponding mdb location")
        exit()

    vid2txt(args)

if __name__ == '__main__':
    main()
