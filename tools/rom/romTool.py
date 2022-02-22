""""
reload(romTool)
rom  = romTool.RomTool()


rom.create_rom(mirror_anim=False,
               step_frame=10,
               exclude_components=['spine', 'neck', 'leg', 'arm', 'hand']
                )
"""

import os
import getpass
import json
import re
from collections import OrderedDict
import pymel.core as pm
import maya.cmds as cmds

ROM_PATH = r'C:\Users\juanp\OneDrive\Documents\maya\pdb_rigLib\tools\rom\templates'
TEMPLATE_NAME = 'biped'
NAME_CONVENTION = 'mgear'

class RomFragment():

    def __init__(self,
                 control,
                 axis=['y', 'z', 'x'],
                 val_list=[[90], [90], [90]],
                 special_attr=[],
                 special_val=[],
                 ):

        # --- args
        self.control = control
        self.axis = axis
        self.val_list = val_list
        self.special_attrs = special_attr
        self.special_vals = special_val

        # --- vars
        self.control_opposite = None
        self.mirror_anim = False
        self.anim_controls = list()
        self.rotate_anim = True
        self.special_anim = False
        self.current_frame = 0

        # --- get required info
        self._control_to_pynode()
        self._attrs_check()

        self._get_control_opposite()

    def _control_to_pynode(self):

        try:
            self.control.__module__
        except:
            # --- replace passed controls with pynodes in case passed controls were strings
            self.control = pm.PyNode(self.control)

        # append  pynode control to have a anim_control by default
        self.anim_controls.append(self.control)

    def _get_control_opposite(self):

        side = self._get_side(self.control)
        if side == 'C': return
        opp_side = 'R' if side == 'L' else 'L'

        opp_control = self._make_opp_ctrl(side, opp_side)

        if pm.objExists(opp_control):
            self.control_opposite = pm.PyNode(opp_control)

    def _get_side(self, ctrl):

        if NAME_CONVENTION == 'mgear':
            return  ctrl.name().encode().split('_')[1][0]

        return ctrl.name().encode().split('_')[0]

    def _make_opp_ctrl(self, side, opp_side):
        """create opposite control name string based on side and opposite side, depending of the name convention"""
        if NAME_CONVENTION == 'mgear':

            ctrl_splited = self.control.name().encode().split('_')
            ctrl_splited[1] = ctrl_splited[1].replace(side, opp_side)

            ctrl_opp_list = [part + '_' for part in ctrl_splited]

            return ''.join(ctrl_opp_list)[:-1]

        ctrl_no_side = self.control.name().encode()[1:]
        return  opp_side + ctrl_no_side

    def _set_key(self, attr, key_frame, value):
        """ set a key for passed control and in case there is a mirror control make a key for that one too"""
        self.anim_controls[0].attr(attr).setKey(time=key_frame, value=value)
        if len(self.anim_controls) > 1:
            self.anim_controls[1].attr(attr).setKey(time=key_frame, value=value)

    def _mirror_check(self):
        """ add the opposite control into the anim_contorls list in case opposite exists """
        if self.mirror_anim:
            if self.control_opposite:
                self.anim_controls.append(self.control_opposite)
        else:
            self.anim_controls = [self.control]

    def _attrs_check(self):

        # check if is possible to make rotation keys
        if not self.axis or not self.val_list:
            self.rotate_anim = False
            pm.warning('# there is not axis or key list passed, cannot make rotation keys')

        if len(self.axis) != len(self.val_list):
            self.rotate_anim = False
            pm.warning('# axis list length should match val_list length, cannot make rotation keys')

        for ax in self.axis:

            if ax not in ['x', 'y', 'z']:
                pm.warning(
                    '# looks like axis "{}" is not a valid axis, cannot make rotation keys'.format(ax.capitalize()))
                break

                keyable = self.control.attr('rotate{}'.format(ax.capitalize())).isKeyable()
                if not keyable:
                    self.rotate_anim = False
                pm.warning(
                    '# looks like axis "{}.rotate{}" is not keyable, cannot make rotation keys'.format(self.control,
                                                                                                       ax.capitalize()))
                break

        # check if special attrs is possible
        if self.special_attrs and self.special_vals:

            if len(self.special_attrs) != len(self.special_vals):
                self.special_anim = False
                pm.warning('# special attr list length does not match values list length, cannot make special keys')

                return
            try:
                for attr in self.special_attrs:
                    keyable = self.control.attr(attr).isKeyable()

                    if not keyable:
                        pm.warning('# "{}" is not keyable in "{}", cannot make special keys'.format(attr, self.control))
                        break

                self.special_anim = True

            except:
                pm.warning('# "{}" is not a valid attribute in "{}"'.format(self.special_attrs, self.control))

    def set_anim(self, current_frame, step_frame, clean_keys=True):
        """
        @type integer
        @param current_frame: frame which the keys for base control will start ( this should be pass in romTool)

        @type integer
        @param step_frame: number of frames between each key

        @type bool
        @param clean_keys: delete keys before apply the new animation

        """
        self._mirror_check()

        # --- delete anim to make sure is clean before create keys
        if clean_keys:
            self.delete_anim()

        key_frame = current_frame

        if self.rotate_anim:
            for ax, vals in zip(self.axis, self.val_list):
                for val in vals:
                    attr = 'rotate{}'.format(ax.capitalize())

                    # --- start anim at zero
                    self._set_key(attr, key_frame, 0)
                    key_frame += step_frame

                    # --- value key
                    self._set_key(attr, key_frame, val)
                    key_frame += step_frame

                    # --- anim back to zero
                    self._set_key(attr, key_frame, 0)

        if self.special_anim:

            for special_attr, special_val in zip(self.special_attrs, self.special_vals):
                # --- start anim at zero
                self._set_key(special_attr, key_frame, 0)
                key_frame += step_frame

                # --- value key
                self._set_key(special_attr, key_frame, special_val)
                key_frame += step_frame

                # --- anim back to zero
                self._set_key(special_attr, key_frame, 0)

        self.current_frame = key_frame

        print('current frame:', self.current_frame)

    def delete_anim(self):

        if self.rotate_anim:
            for ax in self.axis:
                attr = 'rotate{}'.format(ax.capitalize())
                pm.delete(self.anim_controls[0].attr(attr).inputs())

                if self.control_opposite:
                    pm.delete(self.control_opposite.attr(attr).inputs())

        if self.special_anim:
            for attr in self.special_attrs:
                pm.delete(self.anim_controls[0].attr(attr).inputs())

                if self.control_opposite:
                    pm.delete(self.control_opposite.attr(attr).inputs())

    def set_mirror_anim(self, mirror_anim=False):
        self.mirror_anim = mirror_anim


class RomTool():

    def __init__(self):

        # --- vars
        self.start_frame = 0
        self.step_frame = 10  # temporal overwritten by the user in  create_rom function
        self.current_frame = self.start_frame
        self.fragments_dic = dict()  # use to save components out to json
        self.fragments_list = list()  # instance of created frags so will be used in delete_anim func
        self.components_dic = OrderedDict()
        self.rom_dir = None
        self.json_ext = '.json'
        self.components_sorted = list()

        # hardcoded components list to read components in a custom order
        self.components_order = ['leg', 'spine', 'arm', 'hand', 'neck']

        # hardcoded exclude components list to load just what is needed
        self.exclude_components = []  # temporary populated by the user in create_rom function

        self.full_component_anim = {'spine': 0.60, 'neck': 0.60}  # components to have full animation keys at same time

        # required info
        self._get_rom_dir()

    # PRIVATE FUNCTIONS

    def temp_romDic(self):
        """this is being use temporary to save components dic, this should be change or delete later"""
        fragments_dic = OrderedDict()

        # fragments_dic = temp_make_leg(fragments_dic)
        fragments_dic = temp_make_hand(fragments_dic)

        self.fragments_dic = fragments_dic
        print(self.fragments_dic)

    def _sort_components(self):
        """ creates the components list in the wanted order to load the keys"""
        self.components_sorted = list()

        # add first the already orderer components and append later the extra nonlisted components
        for component in self.components_order:
            if component in self.components_dic.keys():
                self.components_sorted.append(component)

        for component in self.components_dic.keys():
            if component not in self.components_sorted:
                self.components_sorted.append(component)

        # exclude components to load just the wanted components
        for component in self.exclude_components:
            if component in self.components_sorted:
                self.components_sorted.remove(component)

    def _get_rom_dir(self):
        self.rom_dir = os.path.join(ROM_PATH, TEMPLATE_NAME)

        if not os.path.exists(self.rom_dir):
            os.makedirs(self.rom_dir)

    def _save_component(self, name):
        # run temp romDic to create the dictionary above so it would be save out as a json
        # this would change later for a better saving function
        self.temp_romDic()

        component_name = '{}{}'.format(name, self.json_ext)
        component_path = os.path.join(self.rom_dir, component_name)

        component_str = json.dumps(self.fragments_dic, indent=4, sort_keys=False)
        output = re.sub(r'\n\s+(\]|\-?\d)', r"\1", component_str)

        with open('{}'.format(component_path), 'w+') as file:
            file.write(str(output))

    def _load_components(self):

        # list all the component in rom directory that ends with .json extension
        components_files = [file for file in os.listdir(self.rom_dir) if file.endswith(self.json_ext)]

        for file in components_files:
            file_path = os.path.join(self.rom_dir, file)

            with open(file_path) as json_file:
                data = json.load(json_file, object_pairs_hook=OrderedDict)

            file_name = file.split(self.json_ext)[0]
            self.components_dic[file_name] = data

        # print(self.components_dic)

    def _make_full_component_anim(self, component, mirror_anim):
        """make the animation for the whole component at same time range"""
        for frag in self.components_dic[component].keys():
            # multiply each value of the val_list for the all anim multiplier
            fixed_list = []
            for val_list in self.components_dic[component][frag]['val_list']:
                fixed_val = []
                fixed_list.append(fixed_val)
                for val in val_list:
                    multiplier = self.full_component_anim[component]
                    fixed_val.append(val * multiplier)

            self.components_dic[component][frag]['val_list'] = fixed_list

            fragment = RomFragment(**self.components_dic[component][frag])
            fragment.set_mirror_anim(mirror_anim)
            fragment.set_anim(current_frame=self.current_frame, step_frame=self.step_frame, clean_keys=False)

        self.current_frame = fragment.current_frame

    # PUBLIC FUNCTIONS

    def create_rom(self, mirror_anim=False, step_frame=10, exclude_components=[]):

        self.current_frame = self.start_frame
        self.step_frame = step_frame
        self.exclude_components = exclude_components

        self._load_components()
        self._sort_components()
        self.delete_anim()

        self.fragments_list = list()
        for component in self.components_sorted:

            # check if the component will have a full animation
            full_anim_state = True if component in self.full_component_anim.keys() else False
            component_len = len(self.components_dic[component].keys())

            for i, frag in enumerate(self.components_dic[component].keys()):
                print('--->', frag)
                fragment = RomFragment(**self.components_dic[component][frag])
                fragment.set_mirror_anim(mirror_anim)
                fragment.set_anim(current_frame=self.current_frame, step_frame=self.step_frame)
                self.current_frame = fragment.current_frame

                if full_anim_state and i + 1 == component_len:
                    self._make_full_component_anim(component, mirror_anim)

                self.fragments_list.append(fragment)

    def delete_anim(self):

        if self.fragments_list:
            for fragment in self.fragments_list:
                fragment.delete_anim()


def temp_make_leg(fragments_dic):
    fragments_dic['hip'] = OrderedDict([('control', 'L_legHipFk_CTL'),
                                        ('axis', ['y', 'z', 'x']),
                                        ('val_list', [[-90, 90], [90], [-90]]),
                                        ('special_attr', []),
                                        ('special_val', []),
                                        ])

    fragments_dic['knee'] = OrderedDict([('control', 'L_legKneeFk_CTL'),
                                         ('axis', ['y']),
                                         ('val_list', [[110]]),
                                         ('special_attr', []),
                                         ('special_val', []),
                                         ])

    fragments_dic['ankle'] = OrderedDict([('control', 'L_legAnkleFk_CTL'),
                                          ('axis', ['x', 'z', 'y']),
                                          ('val_list', [[-45, 45], [50, -50], [45]]),
                                          ('special_attr', []),
                                          ('special_val', []),
                                          ])

    fragments_dic['ball'] = OrderedDict([('control', 'L_footBallBipedFk2_CTL'),
                                         ('axis', ['y']),
                                         ('val_list', [[-40]]),
                                         ('special_attr', []),
                                         ('special_val', []),
                                         ])

    return fragments_dic


def temp_make_hand(fragments_dic):
    thumb_vals = [-15, -25, -45, -90]
    for i in range(4):
        fragments_dic['thumb{}'.format(i)] = OrderedDict([('control', 'L_handThumb{}_CTL'.format(i)),
                                                          ('axis', ['z']),
                                                          ('val_list', [[thumb_vals[i]]]),
                                                          ('special_attr', []),
                                                          ('special_val', []),
                                                          ])

    for fing in ['index', 'mid', 'ring', 'pinky']:
        fing_vals = [15, -90, -90, -90]
        for i in range(4):
            fragments_dic['{}{}'.format(fing, i)] = OrderedDict(
                [('control', 'L_hand{}{}_CTL'.format(fing.capitalize(), i)),
                 ('axis', ['z']),
                 ('val_list', [[fing_vals[i]]]),
                 ('special_attr', []),
                 ('special_val', []),
                 ])

    fragments_dic['handAttrs'] = OrderedDict([('control', 'L_handAttrs_CTL'),
                                              ('axis', ['z']),
                                              ('val_list', [[-30]]),
                                              ('special_attr', []),
                                              ('special_val', []),
                                              ])

    return fragments_dic
