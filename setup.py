#!/usr/bin/env python3
from setuptools import setup

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'skill-hppodcraft.jarbasai=skill_hppodcraft:HPPodcraftSkill'

setup(
    # this is the package name that goes on pip
    name='ovos-skill-hppodcraft',
    version='0.0.1',
    description='ovos hppodcraft skill plugin',
    url='https://github.com/JarbasSkills/skill-hppodcraft',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    package_dir={"skill_hppodcraft": ""},
    package_data={'skill_hppodcraft': ['locale/*', 'ui/*', 'res/*']},
    packages=['skill_hppodcraft'],
    include_package_data=True,
    install_requires=["ovos_workshop~=0.0.5a1"],
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
