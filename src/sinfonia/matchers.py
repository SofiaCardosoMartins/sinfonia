#
# Sinfonia
#
# Copyright (c) 2022 Carnegie Mellon University
#
# SPDX-License-Identifier: MIT
#
"""Tier1 match functions

Plugin setup, additional functions can be added by external python modules
by defining 'sinfonia_tier1_matchers' setuptools entry points.
"""

from __future__ import annotations

import logging
import random
import math
from operator import itemgetter
from typing import Callable, Iterator, List, Sequence

from importlib_metadata import EntryPoint, entry_points

from .client_info import ClientInfo
from .cloudlets import Cloudlet
from .deployment_recipe import DeploymentRecipe

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# Type definition for a Sinfonia Tier1 match function
Tier1MatchFunction = Callable[
    [ClientInfo, DeploymentRecipe, List[Cloudlet]], Iterator[Cloudlet]
]


def get_match_function_plugins() -> dict[str, EntryPoint]:
    """Returns a list of match function plugin entrypoints"""
    return {ep.name: ep for ep in entry_points(group="sinfonia.tier1_matchers")}


def tier1_best_match(
    match_functions: Sequence[Tier1MatchFunction],
    client_info: ClientInfo,
    deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    """Generator which yields cloudlets based on selected matchers."""
    for matcher in match_functions:
        yield from matcher(client_info, deployment_recipe, cloudlets)


# ------------------ Collection of Match functions follows --------------

def match_by_network(
    client_info: ClientInfo,
    _deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    """Yields any cloudlets that claim to be local.
    Also removes cloudlets that explicitly blacklist the client address
    """
    # Used to jump the loop whenever a cloudlet can be removed from the list
    class DropCloudlet(Exception):
        pass

    for cloudlet in cloudlets[:]:
        try:
            for network in cloudlet.rejected_clients:
                if client_info.ipaddress in network:
                    logger.debug("Cloudlet (%s) would reject client", cloudlet.name)
                    raise DropCloudlet

            for network in cloudlet.local_networks:
                if client_info.ipaddress in network:
                    logger.info("network (%s)", cloudlet.name)
                    cloudlets.remove(cloudlet)
                    yield cloudlet

            for network in cloudlet.accepted_clients:
                if client_info.ipaddress not in network:
                    logger.debug("Cloudlet (%s) will not accept client", cloudlet.name)
                    raise DropCloudlet

        except DropCloudlet:
            cloudlets.remove(cloudlet)


def _estimated_rtt(distance_in_km):
    """Estimated RTT based on distance and speed of light
    Only used for logging/debugging.
    """
    speed_of_light = 299792.458
    return 2 * (distance_in_km / speed_of_light)


def match_by_location(
    client_info: ClientInfo,
    _deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    """Yields any geographically close cloudlets"""
    if client_info.location is None:
        return

    by_distance = []

    for cloudlet in cloudlets:
        distance = cloudlet.distance_from(client_info.location)
        if distance is not None:
            by_distance.append((distance, cloudlet))

    if not by_distance:
        return

    by_distance.sort(key=itemgetter(0))
    for distance, cloudlet in by_distance:
        logger.info(
            "distance (%s) %d km, %.3f minRTT",
            cloudlet.name,
            distance,
            _estimated_rtt(distance),
        )
        cloudlets.remove(cloudlet)
        yield cloudlet


def match_random(
    _client_info: ClientInfo,
    _deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    """Shuffle anything that is left and return in randomized order"""
    random.shuffle(cloudlets)
    for cloudlet in cloudlets[:]:
        logger.info("random (%s)", cloudlet.name)
        cloudlets.remove(cloudlet)
        yield cloudlet

def match_resources(
    client_info: ClientInfo,
    _deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    
    
#    for cloudlet in cloudlets:
#        print("LOG: Cloudlet info: ", cloudlet.resources) # dictionary
#        print("LOG: Client info: ", client_info)
    accepted_cloudlets=[]
    for cloudlet in cloudlets[:]:
#        print("LOG: Cloudlet resources: ", cloudlet.resources)
        if(cloudlet.resources["cpu_avail"] >= client_info.resourceReqs["cpu"] and
            cloudlet.resources["mem_avail"] >= client_info.resourceReqs["mem"]
             and cloudlet.resources["disk_avail"] >= client_info.resourceReqs["disk"]):
                accepted_cloudlets.append(cloudlet)
 #               print("LOG: Accept cloudlet ", cloudlet)
        cloudlets.remove(cloudlet)

    print("LOG: Accept cloudlet ", accepted_cloudlets[0])
    yield accepted_cloudlets[0]

def match_best_cpu(
    client_info: ClientInfo,
    _deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    
    cpu_load=[]
    accepted_cloudlets=[]
    for cloudlet in cloudlets[:]:
#        print("LOG: Cloudlet resources: ", cloudlet.resources)
        if(cloudlet.resources["cpu_avail"] >= client_info.resourceReqs["cpu"] and
            cloudlet.resources["mem_avail"] >= client_info.resourceReqs["mem"]
             and cloudlet.resources["disk_avail"] >= client_info.resourceReqs["disk"]):
                cpu_load.append(cloudlet.resources["cpu_used"])
                accepted_cloudlets.append(cloudlet)
 #               print("LOG: Accept cloudlet ", cloudlet)
        cloudlets.remove(cloudlet)

    sorted_cloudlets=[x for _, x in sorted(zip(cpu_load, accepted_cloudlets), key=lambda pair: pair[0], reverse=True)]
    for cloudlet in sorted_cloudlets:
        yield cloudlet
    print("LOG: Accept cloudlet ", sorted_cloudlets[0])
    yield sorted_cloudlets[0]

def match_best_cpu_mem(
    client_info: ClientInfo,
    _deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    
    cpu_mem_load=[]
    accepted_cloudlets=[]
    for cloudlet in cloudlets[:]:
#        print("LOG: Cloudlet resources: ", cloudlet.resources)
        if(cloudlet.resources["cpu_avail"] >= client_info.resourceReqs["cpu"] and
            cloudlet.resources["mem_avail"] >= client_info.resourceReqs["mem"]
             and cloudlet.resources["disk_avail"] >= client_info.resourceReqs["disk"]):
                norm=math.sqrt(pow(cloudlet.resources["cpu_used"],2) + pow(cloudlet.resources["mem_used"],2))
                cpu_mem_load.append(norm)
                accepted_cloudlets.append(cloudlet)
 #               print("LOG: Accept cloudlet ", cloudlet)
        cloudlets.remove(cloudlet)

    sorted_cloudlets=[x for _, x in sorted(zip(cpu_mem_load, accepted_cloudlets), key=lambda pair: pair[0], reverse=True)]
    for cloudlet in sorted_cloudlets:
        yield cloudlet
    print("LOG: Accept cloudlet ", sorted_cloudlets[0])
    yield sorted_cloudlets[0]

def match_balance_cpu_mem(
    client_info: ClientInfo,
    _deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    """Balanced match function based on L2 norm of (cpu, mem) increment"""
    norms=[]
    cloudlets_accepted=[]
    for cloudlet in cloudlets[:]:
        if(cloudlet.resources["cpu_avail"] >= client_info.resourceReqs["cpu"] and
            cloudlet.resources["mem_avail"] >= client_info.resourceReqs["mem"]
                and cloudlet.resources["disk_avail"] >= client_info.resourceReqs["disk"]):
                    cpu_increment=cloudlet.resources["cpu_used"] + client_info.resourceReqs["cpu"]
                    mem_increment=cloudlet.resources["mem_used"] + client_info.resourceReqs["mem"]
                    norm=math.sqrt(pow(cpu_increment,2) + pow(mem_increment,2))
                    norms.append(norm)
                    cloudlets_accepted.append(cloudlet)
        cloudlets.remove(cloudlet)

    # sort cloudlets based on L2 norm
    sorted_cloudlets=[x for _, x in sorted(zip(norms, cloudlets_accepted), key=lambda pair: pair[0])]
    for cloudlet in sorted_cloudlets:
        yield cloudlet
        print("LOG: Accept cloudlet ", cloudlet)

def match_balance_cpu(
    client_info: ClientInfo,
    _deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    """Balanced match function based on L2 norm of (cpu) increment"""
    norms=[]
    cloudlets_accepted=[]
    for cloudlet in cloudlets[:]:
        if(cloudlet.resources["cpu_avail"] >= client_info.resourceReqs["cpu"] and
            cloudlet.resources["mem_avail"] >= client_info.resourceReqs["mem"]
                and cloudlet.resources["disk_avail"] >= client_info.resourceReqs["disk"]):
                    cpu_increment=cloudlet.resources["cpu_used"] + client_info.resourceReqs["cpu"]
                    norm=math.sqrt(pow(cpu_increment,2))
                    norms.append(norm)
                    cloudlets_accepted.append(cloudlet)
        cloudlets.remove(cloudlet)
    
    # sort cloudlets based on L2 norm
    sorted_cloudlets=[x for _, x in sorted(zip(norms, cloudlets_accepted), key=lambda pair: pair[0])]
    sorted_cloudlets=[sorted_cloudlets[0]]
    print("CLOUDLETS: ", sorted_cloudlets, "\n")
	
    for cloudlet in sorted_cloudlets:
        yield cloudlet

def match_balance_mem(
    client_info: ClientInfo,
    _deployment_recipe: DeploymentRecipe,
    cloudlets: list[Cloudlet],
) -> Iterator[Cloudlet]:
    """Balanced match function based on L2 norm of (mem) increment"""
    norms=[]
    cloudlets_accepted=[]
    for cloudlet in cloudlets[:]:
        if(cloudlet.resources["cpu_avail"] >= client_info.resourceReqs["cpu"] and
            cloudlet.resources["mem_avail"] >= client_info.resourceReqs["mem"]
                and cloudlet.resources["disk_avail"] >= client_info.resourceReqs["disk"]):
                    mem_increment=cloudlet.resources["mem_used"] + client_info.resourceReqs["mem"]
                    norm=math.sqrt(pow(mem_increment,2))
                    norms.append(norm)
                    cloudlets_accepted.append(cloudlet)
        cloudlets.remove(cloudlet)

    # sort cloudlets based on L2 norm
    sorted_cloudlets=[x for _, x in sorted(zip(norms, cloudlets_accepted), key=lambda pair: pair[0])]
    for cloudlet in sorted_cloudlets:
        yield cloudlet
