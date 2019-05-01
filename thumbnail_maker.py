# thumbnail_maker.py
import time
import os
import logging
from urllib.parse import urlparse
from urllib.request import urlretrieve
from threading import Thread
from queue import Queue

import PIL
from PIL import Image

FORMAT = "[%(threadName)s, %(asctime)s, %(levelname)s] %(message)s"
logging.basicConfig(filename='logfile.log', level=logging.DEBUG, format = FORMAT)

class ThumbnailMakerService(object):
    def __init__(self, home_dir='.'):
        self.home_dir = home_dir
        self.input_dir = self.home_dir + os.path.sep + 'incoming'
        self.output_dir = self.home_dir + os.path.sep + 'outgoing'
        #Instead of having shared global variable between threads which lead to race conditions, let's have a shared queue and use this 
        # for message passing between the threads.
        self.img_queue = Queue()

    def download_images(self, img_url_list):
        # validate inputs
        if not img_url_list:
            return
        os.makedirs(self.input_dir, exist_ok=True)
        
        logging.info("beginning image downloads")

        start = time.perf_counter()
        for url in img_url_list:
            logging.info("downloading image at URL " + url)
            img_filename = urlparse(url).path.split('/')[-1]
            dest_path = self.input_dir + os.path.sep + img_filename
            urlretrieve(url, dest_path)
            self.img_queue.put(img_filename)
        #Poison Pill Technique so that consumer thread knows that end of input has been reached.
        #Otherwise, as you can see below in the resize method (consumer), the thread will be stuck in infinite loop and won't come out.
        #Now, consumer can check for a null value in the queue and understand that the EOF has been reached from the producer's side.
        self.img_queue.put(None) 
        end = time.perf_counter()

        logging.info("downloaded {} images in {} seconds".format(len(img_url_list), end - start))

    def perform_resizing(self):
        # validate inputs
        os.makedirs(self.output_dir, exist_ok=True)

        logging.info("beginning image resizing")
        target_sizes = [32, 64, 200]
        num_images = len(os.listdir(self.input_dir))

        start = time.perf_counter()
        while True:
            filename = self.img_queue.get()
            if filename:
                logging.info("resizing image {}".format(filename))
                orig_img = Image.open(self.input_dir + os.path.sep + filename)
                for basewidth in target_sizes:
                    img = orig_img
                    # calculate target height of the resized image to maintain the aspect ratio
                    wpercent = (basewidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    # perform resizing
                    img = img.resize((basewidth, hsize), PIL.Image.LANCZOS)
                    
                    # save the resized image to the output dir with a modified file name 
                    new_filename = os.path.splitext(filename)[0] + \
                        '_' + str(basewidth) + os.path.splitext(filename)[1]
                    img.save(self.output_dir + os.path.sep + new_filename)

                os.remove(self.input_dir + os.path.sep + filename)
                self.img_queue.task_done()
                logging.info("resizing image {} completed".format(filename))
            else:
                self.img_queue.task_done()
                break
        end = time.perf_counter()

        logging.info("created {} thumbnails in {} seconds".format(num_images, end - start))

    def make_thumbnails(self, img_url_list):
        logging.info("START make_thumbnails")
        start = time.perf_counter()

        t1 = Thread(target=self.download_images, args=([img_url_list]))
        t2 = Thread(target=self.perform_resizing)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        # Note that here, we are using separate threads for downloading and resiziing, i.e. download and resize operations will be in parallel.
        # But, still, all the individual download actions would still be sequential. Just that download and resize will be in parallel.
        # Thus, not much performance gains are expected, only a little bit.
        end = time.perf_counter()
        logging.info("END make_thumbnails in {} seconds".format(end - start))
    