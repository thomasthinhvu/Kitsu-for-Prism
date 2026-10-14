import os
import sys
import TaskPicker

from qt_compat import *
from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from Prism_Kitsu_Gazu_Functions import *


@err_catcher(name=__name__)
def ReportUpdateInfo(self, created, updated, type_name):
    if len(created) > 0 or len(updated) > 0:
        msgString = ""
        created.sort()
        updated.sort()

        if len(created) > 0:
            msgString += "The following " + type_name + " were created:\n\n"
            for i in created:
                msgString += str(i) + "\n"

        if len(created) > 0 and len(updated) > 0:
            msgString += "\n\n"

        if len(updated) > 0:
            msgString += "The following " + type_name + " were updated:\n\n"
            for i in updated:
                msgString += str(i) + "\n"
    else:
        msgString = "No " + type_name + " were created or updated."

    QMessageBox.information(self.core.messageParent, "Kitsu Sync", msgString)


def DownloadDescription(self, name, description, configName):
    local_description = self.core.getConfig(
        name, "description", config=configName
    )

    if description != local_description:
        if local_description is None:
            return description, True, False
        else:
            return description, False, True

    return False, False, False


def saveID(self, name, id_val, info_location):
    oldID = getID(self, name, info_location)
    if oldID != id_val:
        self.core.setConfig(
            cat=name, param="objID", val=id_val, config=info_location.lower()
        )


def removeID(self, name, info_location):
    self.core.setConfig(
        cat=name, param="objID", delete=True, config=info_location.lower()
    )
    self.core.setConfig(
        cat=name, param="thumbnailID", delete=True, config=info_location.lower()
    )


def getID(self, name, info_location):
    return self.core.getConfig(
        cat=name, param="objID", config=info_location.lower()
    )


def saveThumbnailID(self, name, id_val, info_location):
    oldID = getID(self, name, info_location)
    if oldID != id_val:
        self.core.setConfig(
            name, "thumbnailID", id_val, config=info_location.lower()
        )


def RemoveCanceled(entities):
    return [e for e in entities if not e.get("canceled", False)]


def GetKitsuShots(self):
    connected = self.connectToKitsu()
    if connected is False:
        return False

    ksuShots = []
    user_sync = bool(self.getPrjConfig("usersync", dft=False))

    if self.project_dict.get("production_type") == "tvshow":
        episodes = GetEpisodes(self.project_dict, user=user_sync)
        for episode in episodes:
            sequences = GetSequences(episode, "from_episode", user=user_sync)
            for sequence in sequences:
                shots = GetShots(sequence, "from_sequence", user=user_sync)
                for shot in shots:
                    shot["episode_name"] = episode["name"]
                    shot["sequence_name"] = sequence["name"]
                    ksuShots.append(shot)
    else:
        sequences = GetSequences(
            self.project_dict, "from_project", user=user_sync
        )
        for sequence in sequences:
            shots = GetShots(sequence, "from_sequence", user=user_sync)
            for shot in shots:
                shot["sequence_name"] = sequence["name"]
                ksuShots.append(shot)

    if len(ksuShots) == 0:
        return False

    return RemoveCanceled(ksuShots)


def GetKitsuAssets(self):
    connected = self.connectToKitsu()
    if connected is False:
        return False

    assetTypes = GetAssetTypes()
    ksuAssets = []
    user_sync = bool(self.getPrjConfig("usersync", dft=False))

    for assetType in assetTypes:
        assets = GetAssets(self.project_dict, assetType, user=user_sync)
        for asset in assets:
            ksuAssets.append(asset)

    if len(ksuAssets) == 0:
        return False

    return RemoveCanceled(ksuAssets)


def getPublishTypeDict(self, pType, doStatus=False):
    taskTypes_dict = getTaskTypes()

    taskTypes = []
    for taskType in taskTypes_dict:
        # Gazu đời mới dùng for_entity ("Shot" / "Asset"), đời cũ dùng for_shots (bool)
        if "for_entity" in taskType:
            if taskType["for_entity"] == pType:
                taskTypes.append(taskType)
        elif "for_shots" in taskType:
            if taskType["for_shots"] == (pType == "Shot"):
                taskTypes.append(taskType)
        else:
            taskTypes.append(taskType)

    taskStatuses = gazu.task.all_task_statuses()

    tp = TaskPicker.TaskPicker(
        core=self.core,
        taskTypes_dicts=taskTypes,
        taskStatuses_dicts=taskStatuses,
        doStatus=doStatus,
    )
    tp.exec()

    if tp.picked_data is None or (isinstance(tp.picked_data, list) and tp.picked_data[0] is None):
        QMessageBox.warning(
            self.core.messageParent, "Kitsu Publish", "Publishing canceled"
        )
        if doStatus:
            return [None, None, None, None]
        return None

    return tp.picked_data
