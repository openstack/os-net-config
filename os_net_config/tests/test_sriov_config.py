# -*- coding: utf-8 -*-

# Copyright 2019 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import os.path
import random
import shutil
import tempfile


from os_net_config import sriov_config
from os_net_config.tests import base
from os_net_config import utils


class TestSriovConfig(base.TestCase):
    """Unit tests for methods defined in sriov_config.py"""

    def setUp(self):
        super(TestSriovConfig, self).setUp()
        rand = str(int(random.random() * 100000))

        tmpdir = tempfile.mkdtemp()
        self.stub_out('os_net_config.sriov_config._SYS_CLASS_NET', tmpdir)

        sriov_config._UDEV_RULE_FILE = '/tmp/' + rand + 'etc_udev_rules.d'\
            '80-persistent-os-net-config.rules'
        sriov_config._UDEV_LEGACY_RULE_FILE = '/tmp/' + rand + 'etc_udev_'\
            'rules.d_70-os-net-config-sriov.rules'
        sriov_config._IFUP_LOCAL_FILE = '/tmp/' + rand + 'sbin_ifup-local'
        sriov_config._RESET_SRIOV_RULES_FILE = '/tmp/' + rand + 'etc_udev_'\
            'rules.d_70-tripleo-reset-sriov.rules'
        sriov_config._ALLOCATE_VFS_FILE = '/tmp/' + rand + 'etc_sysconfig_'\
            'allocate_vfs'
        sriov_config._SRIOV_CONFIG_FILE = '/tmp/' + rand + 'sriov_config'\
                                          '.yaml'

    def tearDown(self):
        super(TestSriovConfig, self).tearDown()
        if os.path.isfile(sriov_config._SRIOV_CONFIG_FILE):
            os.remove(sriov_config._SRIOV_CONFIG_FILE)
        if os.path.isfile(sriov_config._IFUP_LOCAL_FILE):
            os.remove(sriov_config._IFUP_LOCAL_FILE)
        shutil.rmtree(sriov_config._SYS_CLASS_NET)
        if os.path.isfile(sriov_config._RESET_SRIOV_RULES_FILE):
            os.remove(sriov_config._RESET_SRIOV_RULES_FILE)
        if os.path.isfile(sriov_config._ALLOCATE_VFS_FILE):
            os.remove(sriov_config._ALLOCATE_VFS_FILE)
        if os.path.isfile(sriov_config._UDEV_LEGACY_RULE_FILE):
            os.remove(sriov_config._UDEV_LEGACY_RULE_FILE)

    def _write_numvfs(self, ifname, numvfs=0):
        os.makedirs(sriov_config._get_dev_path(ifname))
        numvfs_file = sriov_config._get_dev_path(ifname, 'sriov_numvfs')
        with open(numvfs_file, 'w') as f:
            f.write(str(numvfs))

    def _save_action(self, action):
        try:
            self._action_order.append(action)
        except AttributeError:
            self._action_order = [action]

    def setUp_udev_stubs(self):
        def udev_monitor_setup_stub():
            self._save_action('udev_monitor_setup')
            return
        self.stub_out('os_net_config.sriov_config.udev_monitor_setup',
                      udev_monitor_setup_stub)

        def udev_monitor_start_stub(observer):
            self._save_action('udev_monitor_start')
            return
        self.stub_out('os_net_config.sriov_config.udev_monitor_start',
                      udev_monitor_start_stub)

        def udev_monitor_stop_stub(observer):
            self._save_action('udev_monitor_stop')
            return
        self.stub_out('os_net_config.sriov_config.udev_monitor_stop',
                      udev_monitor_stop_stub)

        def trigger_udev_rules_stub():
            self._save_action('trigger_udev_rules')
            return
        self.stub_out('os_net_config.sriov_config.trigger_udev_rules',
                      trigger_udev_rules_stub)

        def reload_udev_rules_stub():
            self._save_action('reload_udev_rules')
            return
        self.stub_out('os_net_config.sriov_config.reload_udev_rules',
                      reload_udev_rules_stub)

    def test_add_udev_rules(self):
        """Test Add udev rules

        """
        def get_pf_pci_stub(name):
            pci_address = {"p2p1": "0000:01:01.0",
                           "p2p2": "0000:01:02.0",
                           "p2p3": "0000:01:03.0"}
            return pci_address[name]
        self.stub_out('os_net_config.sriov_config.get_pf_pci',
                      get_pf_pci_stub)

        self.setUp_udev_stubs()

        exp_udev_content = '# This file is autogenerated by os-net-config\n'\
                           'SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", '\
                           'KERNELS=="0000:01:01.0", NAME="p2p1"\n'

        sriov_config.add_udev_rule_for_sriov_pf("p2p1")
        f = open(sriov_config._UDEV_RULE_FILE, 'r')
        self.assertEqual(exp_udev_content, f.read())

    def test_append_udev_rules(self):
        """Test adding udev rules

        """
        def get_pf_pci_stub(name):
            pci_address = {"p2p1": "0000:01:01.0",
                           "p2p2": "0000:01:02.0",
                           "p2p3": "0000:01:03.0"}
            return pci_address[name]
        self.stub_out('os_net_config.sriov_config.get_pf_pci',
                      get_pf_pci_stub)

        self.setUp_udev_stubs()

        exp_udev_content = '# This file is autogenerated by os-net-config\n'\
                           'SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", '\
                           'KERNELS=="0000:01:01.0", NAME="p2p1"\n' \
                           'SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", '\
                           'KERNELS=="0000:01:02.0", NAME="p2p2"\n'
        udev_content = '# This file is autogenerated by os-net-config\n'\
                       'SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", '\
                       'KERNELS=="0000:01:01.0", NAME="p2p1"\n'
        udev_file = open(sriov_config._UDEV_RULE_FILE, "w")
        udev_file.write(udev_content)
        udev_file.close()
        sriov_config.add_udev_rule_for_sriov_pf("p2p2")
        f = open(sriov_config._UDEV_RULE_FILE, 'r')
        self.assertEqual(exp_udev_content, f.read())

    def test_add_legacy_udev_rules(self):
        """Test Add udev rules for legacy sriov

        """
        self.setUp_udev_stubs()

        exp_udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p1", RUN+="/bin/os-net-config-sriov -n %k:8"\n'
        sriov_config.add_udev_rule_for_legacy_sriov_pf("p2p1", 8)
        f = open(sriov_config._UDEV_LEGACY_RULE_FILE, 'r')
        self.assertEqual(exp_udev_content, f.read())

    def test_modify_legacy_udev_rules(self):
        """Test modifying udev rules for legacy sriov

        """
        self.setUp_udev_stubs()

        udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p1", RUN+="/bin/os-net-config-sriov -n %k:10"\n'\
            'KERNEL=="p2p2", RUN+="/bin/os-net-config-sriov -n %k:12"\n'
        exp_udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p1", RUN+="/bin/os-net-config-sriov -n %k:8"\n'\
            'KERNEL=="p2p2", RUN+="/bin/os-net-config-sriov -n %k:12"\n'
        udev_file = open(sriov_config._UDEV_LEGACY_RULE_FILE, "w")
        udev_file.write(udev_content)
        udev_file.close()
        sriov_config.add_udev_rule_for_legacy_sriov_pf("p2p1", 8)
        f = open(udev_file.name, 'r')
        self.assertEqual(exp_udev_content, f.read())

    def test_same_legacy_udev_rules(self):
        """Test without changing udev rules for legacy sriov

        """
        self.setUp_udev_stubs()

        udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p1", RUN+="/bin/os-net-config-sriov -n %k:8"\n'\
            'KERNEL=="p2p2", RUN+="/bin/os-net-config-sriov -n %k:10"\n'
        exp_udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p1", RUN+="/bin/os-net-config-sriov -n %k:8"\n'\
            'KERNEL=="p2p2", RUN+="/bin/os-net-config-sriov -n %k:10"\n'
        udev_file = open(sriov_config._UDEV_LEGACY_RULE_FILE, "w")
        udev_file.write(udev_content)
        udev_file.close()
        sriov_config.add_udev_rule_for_legacy_sriov_pf("p2p2", 10)
        f = open(udev_file.name, 'r')
        self.assertEqual(exp_udev_content, f.read())

    def test_append_legacy_udev_rules(self):
        """Test appending udev rules for legacy sriov

        """
        self.setUp_udev_stubs()

        udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p1", RUN+="/bin/os-net-config-sriov -n %k:8"\n'\
            'KERNEL=="p2p2", RUN+="/bin/os-net-config-sriov -n %k:10"\n'
        exp_udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p1", RUN+="/bin/os-net-config-sriov -n %k:8"\n'\
            'KERNEL=="p2p2", RUN+="/bin/os-net-config-sriov -n %k:10"\n' \
            'KERNEL=="p2p3", RUN+="/bin/os-net-config-sriov -n %k:12"\n'
        udev_file = open(sriov_config._UDEV_LEGACY_RULE_FILE, "w")
        udev_file.write(udev_content)
        udev_file.close()
        sriov_config.add_udev_rule_for_legacy_sriov_pf("p2p3", 12)
        f = open(udev_file.name, 'r')
        self.assertEqual(exp_udev_content, f.read())

    def setUp_pf_stubs(self, vendor_id="0x8086"):
        run_cmd = []
        self.setUp_udev_stubs()

        def run_ip_config_cmd_stub(*args, **kwargs):
            run_cmd.append(' '.join(args))
        self.stub_out('os_net_config.sriov_config.run_ip_config_cmd',
                      run_ip_config_cmd_stub)

        def cleanup_puppet_config_stub():
            return
        self.stub_out('os_net_config.sriov_config.cleanup_puppet_config',
                      cleanup_puppet_config_stub)

        def _wait_for_vf_creation_stub(pf_name, numvfs):
            self._save_action('_wait_for_vf_creation_stub')
            return
        self.stub_out('os_net_config.sriov_config._wait_for_vf_creation',
                      _wait_for_vf_creation_stub)

        def get_vendor_id_stub(ifname):
            return vendor_id
        self.stub_out('os_net_config.sriov_config.get_vendor_id',
                      get_vendor_id_stub)

        def configure_switchdev_stub(pf_name):
            self._save_action('configure_switchdev')
            return
        self.stub_out('os_net_config.sriov_config.configure_switchdev',
                      configure_switchdev_stub)

        self.set_numvfs = sriov_config.set_numvfs
        self.get_numvfs = sriov_config.get_numvfs

        def get_numvfs_stub(*args):
            self._save_action('get_numvfs')
            return self.get_numvfs(*args)
        self.stub_out('os_net_config.sriov_config.get_numvfs',
                      get_numvfs_stub)

        def set_numvfs_stub(*args):
            self._save_action('set_numvfs')
            return self.set_numvfs(*args)
        self.stub_out('os_net_config.sriov_config.set_numvfs',
                      set_numvfs_stub)

    def test_configure_sriov_pf(self):
        """Test the numvfs setting for SR-IOV PF

        Test the udev rules created for legacy mode of SR-IOV PF
        """

        exp_udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p1", RUN+="/bin/os-net-config-sriov -n %k:10"\n'\
            'KERNEL=="p2p2", RUN+="/bin/os-net-config-sriov -n %k:12"\n'

        run_cmd = []

        self.setUp_udev_stubs()

        def run_ip_config_cmd_stub(*args, **kwargs):
            run_cmd.append(' '.join(args))
        self.stub_out('os_net_config.sriov_config.run_ip_config_cmd',
                      run_ip_config_cmd_stub)

        def _wait_for_vf_creation_stub(pf_name, numvfs):
            numvfs_pair = {"p2p1": 10, "p2p2": 12}
            self.assertEqual(numvfs_pair[pf_name], numvfs)
        self.stub_out('os_net_config.sriov_config._wait_for_vf_creation',
                      _wait_for_vf_creation_stub)

        def get_vendor_id_stub(ifname):
            return "0x8086"
        self.stub_out('os_net_config.sriov_config.get_vendor_id',
                      get_vendor_id_stub)

        pf_config = [{"device_type": "pf", "name": "p2p1", "numvfs": 10,
                      "promisc": "on", "link_mode": "legacy"},
                     {"device_type": "pf", "name": "p2p2", "numvfs": 12,
                      "promisc": "off", "link_mode": "legacy"}]

        for ifname in ['p2p1', 'p2p2']:
            self._write_numvfs(ifname)

        utils.write_yaml_config(sriov_config._SRIOV_CONFIG_FILE, pf_config)
        sriov_config.configure_logger(debug=True)
        sriov_config.configure_sriov_pf()

        f = open(sriov_config._UDEV_LEGACY_RULE_FILE, 'r')
        self.assertEqual(exp_udev_content, f.read())
        self.assertEqual(10, sriov_config.get_numvfs('p2p1'))
        self.assertEqual(12, sriov_config.get_numvfs('p2p2'))

    def test_configure_sriov_pf_nicpart(self):
        """Test the udev rules created for legacy mode of SR-IOV PF

        In this case, the VF(s) are already bound/attached
        """

        self.setUp_pf_stubs()

        exp_udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p2", RUN+="/bin/os-net-config-sriov -n %k:12"\n'
        exp_actions = [
            'udev_monitor_setup',
            'udev_monitor_start',
            'set_numvfs',
            'get_numvfs',
            '_wait_for_vf_creation_stub',
            'get_numvfs',
            'reload_udev_rules',
            'set_numvfs',
            'get_numvfs',
            '_wait_for_vf_creation_stub',
            'get_numvfs',
            'udev_monitor_stop',
        ]

        pf_config = [{"device_type": "pf", "name": "p2p1", "numvfs": 10,
                      "promisc": "on", "link_mode": "legacy"},
                     {"device_type": "pf", "name": "p2p2", "numvfs": 12,
                      "promisc": "off", "link_mode": "legacy"},
                     {"device": {"name": "p2p1", "vfid": 0},
                      "device_type": "vf", "name": "p2p1v0", "max_tx_rate": 0,
                      "min_tx_rate": 0, "pci_address": "0000:18:0a.0",
                      "trust": "on", "spoofcheck": "off"}]

        for ifname in ['p2p1', 'p2p2']:
            self._write_numvfs(ifname)

        self._action_order = []
        utils.write_yaml_config(sriov_config._SRIOV_CONFIG_FILE, pf_config)
        sriov_config.configure_logger(debug=True)
        sriov_config.configure_sriov_pf()
        self.assertEqual(exp_actions, self._action_order)
        f = open(sriov_config._UDEV_LEGACY_RULE_FILE, 'r')
        self.assertEqual(exp_udev_content, f.read())
        self.assertEqual(12, sriov_config.get_numvfs('p2p2'))

    def test_configure_sriov_pf_non_nicpart(self):
        """Test the udev rules created for legacy mode of SR-IOV PF

        In this case, the nic partitioned VF(s) are not attached
        """

        self.setUp_pf_stubs()

        exp_udev_content = '# This file is autogenerated by os-net-config\n'\
            'KERNEL=="p2p1", RUN+="/bin/os-net-config-sriov -n %k:10"\n'\
            'KERNEL=="p2p2", RUN+="/bin/os-net-config-sriov -n %k:12"\n'
        exp_actions = [
            'udev_monitor_setup',
            'udev_monitor_start',
            'reload_udev_rules',
            'set_numvfs',
            'get_numvfs',
            '_wait_for_vf_creation_stub',
            'get_numvfs',
            'reload_udev_rules',
            'set_numvfs',
            'get_numvfs',
            '_wait_for_vf_creation_stub',
            'get_numvfs',
            'udev_monitor_stop',
        ]

        pf_config = [{"device_type": "pf", "name": "p2p1", "numvfs": 10,
                      "promisc": "on", "link_mode": "legacy"},
                     {"device_type": "pf", "name": "p2p2", "numvfs": 12,
                      "promisc": "off", "link_mode": "legacy"},
                     {"device": {"name": "eno3", "vfid": 1},
                      "device_type": "vf", "name": "eno3v0", "max_tx_rate": 0,
                      "min_tx_rate": 0, "pci_address": "0000:18:0e.1",
                      "trust": "on", "spoofcheck": "off"}]

        for ifname in ['p2p1', 'p2p2']:
            self._write_numvfs(ifname)

        self._action_order = []
        utils.write_yaml_config(sriov_config._SRIOV_CONFIG_FILE, pf_config)
        sriov_config.configure_logger(debug=True)
        sriov_config.configure_sriov_pf()
        self.assertEqual(exp_actions, self._action_order)
        f = open(sriov_config._UDEV_LEGACY_RULE_FILE, 'r')
        self.assertEqual(exp_udev_content, f.read())
        self.assertEqual(10, sriov_config.get_numvfs('p2p1'))
        self.assertEqual(12, sriov_config.get_numvfs('p2p2'))

    def test_cleanup_puppet_config_deprecation(self):
        """Test the cleanup of puppet-tripleo generated config file.

        Usecase: The ifup-local has the default content generated by
        puppet-tripleo
        """

        content = '#!/bin/bash\n'\
                  '/etc/sysconfig/allocate_vfs $1'
        f = open(sriov_config._RESET_SRIOV_RULES_FILE, "w+")
        f.close()
        f = open(sriov_config._ALLOCATE_VFS_FILE, "w+")
        f.close()
        f = open(sriov_config._IFUP_LOCAL_FILE, "w+")
        f.write(content)
        f.close()

        sriov_config.cleanup_puppet_config()
        self.assertEqual(False,
                         os.path.exists(sriov_config._RESET_SRIOV_RULES_FILE))
        self.assertEqual(False,
                         os.path.exists(sriov_config._ALLOCATE_VFS_FILE))
        self.assertEqual(False,
                         os.path.exists(sriov_config._IFUP_LOCAL_FILE))

    def test_cleanup_puppet_config_new(self):
        """Test the cleanup of puppet-tripleo generated config file.

        Usecase: When os-net-config is run on fresh deployments, all these
        files will not exist.
        """

        sriov_config.cleanup_puppet_config()
        self.assertEqual(False,
                         os.path.exists(sriov_config._RESET_SRIOV_RULES_FILE))
        self.assertEqual(False,
                         os.path.exists(sriov_config._ALLOCATE_VFS_FILE))
        self.assertEqual(False,
                         os.path.exists(sriov_config._IFUP_LOCAL_FILE))

    def test_cleanup_puppet_config_modified(self):
        """Test the cleanup of puppet-tripleo generated config file

        Usecase: When os-net-config is run first time after the deprecation
        of NeutronSriovNumVFs and ifup-local has contents other than invoking
        allocate_vfs.
        """

        content = '#!/bin/bash\n'\
                  '/etc/sysconfig/allocate_vfs $1\n'\
                  '/usr/sbin/ifup eth0'
        mod_content = '#!/bin/bash\n'\
                      '/usr/sbin/ifup eth0'
        f = open(sriov_config._IFUP_LOCAL_FILE, "w+")
        f.write(content)
        f.close()

        sriov_config.cleanup_puppet_config()
        self.assertEqual(False,
                         os.path.exists(sriov_config._RESET_SRIOV_RULES_FILE))
        self.assertEqual(False,
                         os.path.exists(sriov_config._ALLOCATE_VFS_FILE))
        self.assertEqual(True,
                         os.path.exists(sriov_config._IFUP_LOCAL_FILE))

        f = open(sriov_config._IFUP_LOCAL_FILE, "r")
        self.assertEqual(mod_content, f.read())

    def test_numvfs_config(self):
        """Test the numvfs config with valid arguments"""

        self._write_numvfs('p2p1')
        self.assertEqual(None, sriov_config.main(['ARG0', '-n', 'p2p1:15']))
        self.assertEqual(15, sriov_config.get_numvfs('p2p1'))

    def test_numvfs_invalid_params(self):
        """Test the numvfs config with invalid arguments"""

        self._write_numvfs('p2p1')
        self.assertEqual(1, sriov_config.main(['ARG0', '-n', 'p2p1:15a']))
        self.assertEqual(0, sriov_config.get_numvfs('p2p1'))

    def test_numvfs_preconfigured(self):
        """Test the numvfs config while its already configured"""

        self._write_numvfs('p2p1', 10)
        self.assertEqual(None, sriov_config.main(['ARG0', '-n', 'p2p1:15']))
        self.assertEqual(10, sriov_config.get_numvfs('p2p1'))

    def test_configure_sriov_vf(self):
        """Test configuration of SR-IOV VF settings"""

        vf_config = [{"device_type": "vf", "device": {"name": "p2p1",
                      "vfid": 1}, "promisc": "on", "vlan_id": 101,
                      "qos": 5, "macaddr": "AA:BB:CC:DD:EE:FF",
                      "spoofcheck": "on", "state": "auto", "trust": "on",
                      "min_tx_rate": 0, "max_tx_rate": 100,
                      "name": "p2p1_1"}]
        exp_cmds = ["ip link set dev p2p1 vf 1 mac AA:BB:CC:DD:EE:FF",
                    "ip link set dev p2p1 vf 1 vlan 101 qos 5",
                    "ip link set dev p2p1 vf 1 min_tx_rate 0",
                    "ip link set dev p2p1 vf 1 max_tx_rate 100",
                    "ip link set dev p2p1_1 promisc on",
                    "ip link set dev p2p1 vf 1 spoofchk on",
                    "ip link set dev p2p1 vf 1 state auto",
                    "ip link set dev p2p1 vf 1 trust on"]
        run_cmd = []

        def run_ip_config_cmd_stub(*args, **kwargs):
            run_cmd.append(' '.join(args))
        self.stub_out('os_net_config.sriov_config.run_ip_config_cmd',
                      run_ip_config_cmd_stub)

        utils.write_yaml_config(sriov_config._SRIOV_CONFIG_FILE, vf_config)
        sriov_config.configure_sriov_vf()

        for cmd in exp_cmds:
            self.assertIn(cmd, run_cmd)
