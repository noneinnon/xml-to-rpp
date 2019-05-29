import xml.etree.ElementTree as ET
import os


class Converter:
    def __init__(self, filestring):
        self.filestring = filestring
        self.tree = ET.fromstring(filestring)
        #self.output = os.path.splitext(os.path.basename(filestring))[0] + '.rpp'
        self.framerate = int(self.tree.find('sequence/rate/timebase').text)
        self.sample_rate = 480000
    # Divides frames by framerate to get seconds, rounds to 14 decimal

    def rounder(self, integer):
        return round(integer / self.framerate, 14)

    def media_items(self):
        video_file_dict = {}
        audio_file_dict = {}

        # Parses for each video file used in sequence
        for track in self.tree.findall('sequence/media/video/track'):
            for clipitem in (track.iterfind('clipitem')):
                try:
                    pathurl = clipitem.find('file/pathurl').text.replace("%20", " ")
                except:
                    pass
                video_file_dict[clipitem.find('name').text] = pathurl

        # Parses for each audio file used in sequence
        for track in self.tree.findall('sequence/media/audio/track'):
            for clipitem in (track.iterfind('clipitem')):
                # print(clipitem.find('name').text)
                try:
                    pathurl = clipitem.find('file/pathurl').text.replace("%20", " ")
                except:
                    pass
                audio_file_dict[clipitem.find('name').text] = pathurl
        return video_file_dict, audio_file_dict

        # Reaper <track> tag in RPP file
    def reaper_track(self, track_counter):
        string = '''
        <TRACK
            NAME "{name}"
            PEAKCOL 16576
            BEAT -1
            AUTOMODE 0
            VOLPAN 1 0 -1 -1 1
            MUTESOLO 0 0 0
            IPHASE 0
            ISBUS 0 0
            BUSCOMP 0 0
            SHOWINMIX 1 0.6667 0.5 1 0.5 0 0 0
            FREEMODE 0
            SEL 0
            REC 0 0 0 0 0 0 0
            VU 2
            TRACKHEIGHT 24 0 0
            INQ 0 0 0 0.5 100 0 0 100
            NCHAN 2
            FX 1
            TRACKID
            PERF 0
            MIDIOUT -1
            MAINSEND 1 0
            <FXCHAIN
              SHOW 0
              LASTSEL 0
              DOCKED 0
            >
    '''.format(name=track_counter)
        return string
    # Reaper <item> tag in RPP file

    def reaper_item(self, dict, clip_id):
        string = '''
            <ITEM
                POSITION {start}
                SNAPOFFS 0
                LENGTH {length}
                LOOP 1
                ALLTAKES 0
                FADEIN 1 0.01 0 1 0 0
                FADEOUT 1 0.01 0 1 0 0
                MUTE {enabled}
                SEL 1
                IGUID
                IID {id}
                NAME "{name}"
                VOLPAN 1 0 1 -1
                SOFFS {clip_in}
                PLAYRATE 1 1 0 -1 0 0.0025
                CHANMODE 0
                GUID
                <SOURCE WAVE
                FILE "{path}"
                >
            >
    '''.format(
            start=dict["start"],
            name=dict['name'],
            path=dict['name'],
            length=(dict['end'] - dict['start']),
            clip_in=dict['in'],
            enabled=not dict["enabled"],
            id=clip_id)
        return string

    def create_tag_dict(self, clipitem):
        tag_dict = {}
        tag_name_list = ['name', 'duration', 'start', 'end', 'in', 'enabled']
        for each in clipitem:
            if each.tag in tag_name_list:
                if each.text.isdigit():
                    tag_dict[each.tag] = self.rounder(int(each.text))
                elif each.tag == "enabled":
                    tag_dict[each.tag] = int(bool(each.text))
                elif each.tag == "name":
                    tag_dict[each.tag] = each.text
        return tag_dict

    def convert(self, output_path):

        with open(os.path.join(output_path, self.output), 'w') as f:
                # Iterate over each track
            with open('head.rpp', 'r') as head:
                for line in head:
                    f.write(line)
            for track_counter, track in enumerate(self.tree.findall('sequence/media/audio/track')):
                f.write(self.reaper_track(track_counter + 1))
                for counter, clipitem in enumerate(track.iterfind('clipitem')):
                    # collects item data and media info
                    clip_id = counter + 1
                    clip_dict = self.create_tag_dict(clipitem)
                    # Writes to formatted Reaper <ITEM> string
                    f.write(self.reaper_item(clip_dict, clip_id))
                f.write(
                    '''
            >
                    ''')
            with open('bottom.rpp', 'r') as bottom:
                for line in bottom:
                    f.write(line)

    def convert_to_string(self):

        with open('head.rpp', 'r') as head:
            string = "".join(head.readlines())
        for track_counter, track in enumerate(self.tree.findall('sequence/media/audio/track')):
            string = string + self.reaper_track(track_counter + 1)
            for counter, clipitem in enumerate(track.iterfind('clipitem')):
                    # collects item data and media info
                clip_id = counter + 1
                clip_dict = self.create_tag_dict(clipitem)
                # Writes to formatted Reaper <ITEM> string
                string = string + self.reaper_item(clip_dict, clip_id)
            string = string + '''            >'''
        with open('bottom.rpp', 'r') as bottom:
            string = string + "".join(bottom.readlines())
        #string = string.replace("\n", "\r\n")
        return string

    # def announce(self, media_items):
    #     video_files = []
    #     for mediaitem in media_items[0].keys():

    #         if mediaitem in media_items[1].keys():
    #             video_files.append(mediaitem)

    #     if len(video_files) > 0:
    #         for file in video_files:
    #             print(file + ' -----' + ' copy this file into .rpp project folder.')
