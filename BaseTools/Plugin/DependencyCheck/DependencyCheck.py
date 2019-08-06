# @file DependencyCheck.py
# Simple Project Mu Build Plugin to support
# checking package dependencies for all INFs
# in a given package.
##
# Copyright (c) Microsoft Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
##

import logging
from MuEnvironment.PluginManager import IMuBuildPlugin
import os
from MuPythonLibrary.Uefi.EdkII.Parsers.InfParser import InfParser


class DependencyCheck(IMuBuildPlugin):

    def GetTestName(self, packagename, environment):
        return ("MuBuild PackageDependency " + packagename, "MuBuild.PackageDependency." + packagename)

    #   - package is the edk2 path to package.  This means workspace/packagepath relative.
    #   - edk2path object configured with workspace and packages path
    #   - any additional command line args
    #   - RepoConfig Object (dict) for the build
    #   - PkgConfig Object (dict) for the pkg
    #   - EnvConfig Object
    #   - Plugin Manager Instance
    #   - Plugin Helper Obj Instance
    #   - testcase Object used for outputing junit results
    #   - output_stream the StringIO output stream from this plugin
    def RunBuildPlugin(self, packagename, Edk2pathObj, args, repoconfig, pkgconfig, environment, PLM, PLMHelper, tc, output_stream = None):
        overall_status = 0

        # Get current platform
        abs_pkg_path = Edk2pathObj.GetAbsolutePathOnThisSytemFromEdk2RelativePath(packagename)

        # Get INF Files
        INFFiles = self.WalkDirectoryForExtension([".inf"], abs_pkg_path)
        INFFiles = [x.lower() for x in INFFiles]
        INFFiles = [Edk2pathObj.GetEdk2RelativePathFromAbsolutePath(x) for x in INFFiles]  # make edk2relative path so can compare with Ignore List

        # Remove ignored INFs
        if "IgnoreInf" in pkgconfig:
            for a in pkgconfig["IgnoreInf"]:
                a = a.lower().replace(os.sep, "/")
                try:
                    INFFiles.remove(a)
                    tc.LogStdOut("IgnoreInf {0}".format(a))
                except:
                    logging.info("DependencyConfig.IgnoreInf -> {0} not found in filesystem.  Invalid ignore file".format(a))
                    tc.LogStdError("DependencyConfig.IgnoreInf -> {0} not found in filesystem.  Invalid ignore file".format(a))

        # For each INF file
        for file in INFFiles:
            ip = InfParser()
            ip.SetBaseAbsPath(Edk2pathObj.WorkspacePath).SetPackagePaths(Edk2pathObj.PackagePathList).ParseFile(file)

            for p in ip.PackagesUsed:
                if "AcceptableDependencies" in pkgconfig and p not in pkgconfig["AcceptableDependencies"]:
                    logging.error("Dependency Check: Invalid Dependency INF: {0} depends on pkg {1}".format(file, p))
                    tc.LogStdError("Dependency Check: Invalid Dependency INF: {0} depends on pkg {1}".format(file, p))
                    overall_status += 1
        if "AcceptableDependencies" in pkgconfig:
            for a in pkgconfig["AcceptableDependencies"]:
                tc.LogStdOut("Acceptable Package Dependency: {0}".format(a))

        # If XML object exists, add results
        if overall_status is not 0:
            tc.SetFailed("Failed with {0} errors".format(overall_status), "DEPENDENCYCHECK_FAILED")
        else:
            tc.SetSuccess()
        return overall_status

    def ValidateConfig(self, config, name):
        validOptions = ["AcceptableDependencies", "skip", "IgnoreInf"]
        for key in config:
            if key not in validOptions:
                raise Exception("Invalid config option {0} in {1}".format(key, name))
