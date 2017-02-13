#! /usr/bin/env python
import argparse
from PIL import Image
import cv2
from jinja2 import Template

def extract_frames(video_file_name):
    vidcap = cv2.VideoCapture(video_file_name)
    success, image = vidcap.read()
    count = 0
    success = True
    frames = []
    fps = vidcap.get(cv2.cv.CV_CAP_PROP_FPS)
    frame_interval = 1.0/fps * 1000

    while success:
        success, image = vidcap.read()
        frames.append(image)
        count += 1

    print("Writing %d frames @ %d fps" % (count, fps))
    return frames, frame_interval

def write_frames_to_files(video_file_name, frames, out_dir):
    count = 0
    for frame in frames:
        #print("Writing file " + out_dir + video_file_name + '.frame%d.jpg' % count)
        cv2.imwrite(out_dir + video_file_name + '.frame%d.jpg' % count, frame)
        count += 1

def frames2txt(frames, maxLen=80):
    try:
        maxLen = int(maxLen)
    except:
        maxLen = 80

    chs = "#MNHQ$OC?7>!:-;. "
    #chs = "  ..;-:!>7?irl+heaqpdb0wgm@"[::-1]

    txt_images = []
    for frame in frames:
        if frame is None:
            continue
        height, width, x = frame.shape
        rate = float(maxLen) / max(width, height)
        width = int(rate * width)
        height = int(rate * height)

        im = Image.fromarray(frame)
        im = im.resize((width, height))
        string = ''
        for h in range(height):
            for w in range(width):
                rgb = im.getpixel((w, h))
                string += chs[int(sum(rgb) / 3.0 / 256.0 * len(chs))]
            string += '\n'
        txt_images.append(string)
    
    return txt_images

def write_txt_frames_to_files(video_file_name, txt_frames, out_dir):
    count = 0
    for frame in txt_frames:
        #print("Writing file " + out_dir + video_file_name + '.frame%d.txt' % count)
        with open(out_dir + video_file_name + '.frame%d.txt' % count, 'w') as txt_file:
            txt_file.write(frame)
        count += 1
    print("Wrote %d txt images to directory %s" % (len(txt_frames), out_dir))

def write_txt_frames_to_html(out_filename, txt_frames, frame_interval):
    with open('template.jinja') as tpl_f:
        template = Template(tpl_f.read())
        html = template.render(strings=txt_frames, frame_interval=frame_interval)
    with open(out_filename, 'w') as out_f:
        out_f.write(html)
    print("Finished writing html file %s" % out_filename)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('filename', help='Mp4 input file')
    parser.add_argument('-m', '--maxLen', type=int, help='Max width of the output txt video')
    parser.add_argument('-o', '--output', help='Name of the output directory')
    parser.add_argument('-html', '--html', help='Name of the html output file')
    args = parser.parse_args()

    if not args.maxLen:
        args.maxLen = 80
    if not args.output:
        args.output = 'images/'
    
    frames, frame_interval = extract_frames(args.filename)
    txt_frames = frames2txt(frames, args.maxLen)
    write_txt_frames_to_files(args.filename, txt_frames, args.output)
    if args.html:
        write_txt_frames_to_html(args.html, txt_frames, frame_interval)

if __name__ == '__main__':
    main()
