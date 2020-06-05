import os
from operator import itemgetter
import exifread
import sys
from datetime import datetime, timedelta


START_OF_DAY = 5  # AM (hour at which the day starts)
TIME_THRESHOLD = 0.5  # hours


def check_date_affected_by_night(time):
    """If the time the photo was taken at is before 5 AM,
    it counts as the day before, so return a string of the day by my logic"""
    if time.hour < START_OF_DAY:
        # Return a string of the date of the previous day
        return (time - timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        # Return a string of the date
        return time.strftime('%Y-%m-%d')


def create_dir_and_move_to_dir(filepath, filename, folderdate, secondary_index):
    if secondary_index != 0:
        folderdate += ' %d' % secondary_index

    sourcefile = os.path.join(filepath, filename)
    destfile = os.path.join(filepath, folderdate, filename)

    print '%s trying to move to %s' % (sourcefile, destfile)

    if not os.path.exists(os.path.join(filepath, folderdate)):
        os.mkdir(os.path.join(filepath, folderdate))
    os.rename(sourcefile, destfile)


def get_dir_to_scan():
    if len(sys.argv) < 2:
        print 'Usage: group_nikon_photos_by_date.py [directory to scan]'
        return None

    return sys.argv[1]


def get_exif_datetime(full_file_path):
    # Read the file EXIF and return the Date Taken value
    exif_content = exifread.process_file(open(full_file_path, 'rb'))

    if 'EXIF DateTimeOriginal' in exif_content:
        # Parse the datetime string from the EXIF into a datetime object
        return datetime.strptime(str(exif_content['EXIF DateTimeOriginal']), '%Y:%m:%d %H:%M:%S')
    elif 'Image DateTime' in exif_content:
        return datetime.strptime(str(exif_content['Image DateTime']), '%Y:%m:%d %H:%M:%S')
        # This elif takes care of L16 images, that don't have EXIF DateTimeOriginal. They have Image DateTime.
    else:
        return datetime.fromtimestamp(os.path.getmtime(full_file_path))
        #videos

def sorted_file_list(dir_to_scan):
    """
    Creates a sorted file list, not exactly as the name suggests
    """

    file_list = os.listdir(dir_to_scan)
    photos_list = []

    for filename in file_list:
        full_file_path = os.path.join(dir_to_scan, filename)

        # Make sure this is a file and not a directory
        if not os.path.isfile(full_file_path):
            continue  # continue = Skips this file

        current_file_exif = get_exif_datetime(full_file_path)
        print full_file_path, current_file_exif
        photos_list.append((full_file_path, current_file_exif))

    photos_list.sort(key=itemgetter(1))
    return photos_list


def main():
    secondary_index = 0
    number_of_files = 0
    previous_datetime = None
    time_started = datetime.now()

    dir_to_scan = get_dir_to_scan()
    if dir_to_scan is None:
        return

    for full_file_path, exif_datetime in sorted_file_list(dir_to_scan):
        number_of_files += 1  # This is for the statistics at the end

        if previous_datetime is not None:  # If it's not the first file in the directory
            if exif_datetime - previous_datetime > timedelta(hours=TIME_THRESHOLD):  # If the photo was taken more than TIME_THRESHOLD hours later...
                if check_date_affected_by_night(exif_datetime) == check_date_affected_by_night(previous_datetime):
                    secondary_index += 1
                    print 'New event! Raising secondary index.'
                else:
                    secondary_index = 0

        previous_datetime = exif_datetime
        create_dir_and_move_to_dir(dir_to_scan, os.path.basename(full_file_path), check_date_affected_by_night(exif_datetime), secondary_index)

    print 'Processed %d files in %s' % (number_of_files, datetime.now() - time_started)
    raw_input('Press Enter to exit.')


if __name__ == '__main__':
    main()
