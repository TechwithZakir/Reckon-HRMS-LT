# Copyright (c) 2026, Reckon Technologies Ltd.
# Website: www.reckon.tech
# Email: hello@reckon.tech
# For license information, please see license.txt

from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __init__.py
from reckon_hrms_lt import __version__ as version

setup(
	name="reckon_hrms_lt",
	version=version,
	description="Simple HRMS application for Frappe/ERPNext v16",
	author="Reckon Technologies Ltd.",
	author_email="hello@reckon.tech",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
	python_requires=">=3.10",
)
