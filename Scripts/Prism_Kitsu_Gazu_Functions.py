import os
import gazu

from qt_compat import *
from Prism_Kitsu_Tools_Functions import *


def Connect(self, host, user, password, projectName, silent=False):
    """Log-in to Kitsu / Zou API and return project_dict or None."""
     parent = getattr(self.core, "messageParent", None) or QWidget()

    if self.tokens is None:
        try:
            host = normalize_host(host)
            gazu.set_host(host)
            if not gazu.client.host_is_up():
                raise ConnectionError(
                    "Could not connect to the server. Is the host URL correct?"
                )
        except Exception as exc:
            if not silent:
                QMessageBox.warning(parent, "Kitsu Error", str(exc))
            return None

        try:
            self.tokens = gazu.log_in(user, password)
        except Exception:
            message = (
                "Login verification failed.\n"
                "Please ensure your username and password for Kitsu are correct."
            )
            if not silent:
                QMessageBox.warning(parent, "Kitsu Error", message)
            return None

    try:
        project_dict = gazu.project.get_project_by_name(projectName)
    except Exception as exc:
        if not silent:
            QMessageBox.warning(parent, "Kitsu Error", str(exc))
        return None

    if project_dict is None:
        if not silent:
            QMessageBox.warning(
                parent,
                "Kitsu Error",
                "The project could not be found on the Kitsu server.\n"
                "Please verify the project name or your Kitsu permissions.",
            )
        return None

    if not silent:
        QMessageBox.information(parent, "Kitsu Logged in", "Logged in successfully!")

    return project_dict


def removeLastSlash(adress):
    if adress[-1:] == "/":
        adress = adress[:-1]
    return adress


def normalize_host(address):
    """Return a normalized Kitsu API root without duplicated /api suffixes."""
    if not address:
        raise ValueError("Kitsu host is empty. Please enter a server URL.")

    cleaned = address.strip()
    if cleaned.lower().endswith("/api"):
        cleaned = cleaned[:-4]

    cleaned = removeLastSlash(cleaned)
    return cleaned + "/api"


def GetUrl(obj_id, section):
    if section == "project":
        url = gazu.project.get_project_url(obj_id, "shots")
    elif section == "shot":
        obj_dict = gazu.shot.get_shot(obj_id)
        url = gazu.shot.get_shot_url(obj_dict)
    elif section == "asset":
        obj_dict = gazu.asset.get_asset(obj_id)
        url = gazu.asset.get_asset_url(obj_dict)
    else:
        url = ""
    return url


def GetEpisodes(project_dict, user=False):
    if user:
        return gazu.user.all_episodes_for_project(project_dict)
    return gazu.shot.all_episodes_for_project(project_dict)


def GetEpisodeByName(project_dict, episode_name):
    return gazu.shot.get_episode_by_name(project_dict, episode_name)


def RemoveEpisode(episode_dict):
    return gazu.shot.remove_episode(episode_dict)


def GetSequences(dict_obj, where="from_project", user=False):
    if user:
        if where == "from_project":
            return gazu.user.all_sequences_for_project(dict_obj)
        return gazu.user.all_sequences_for_episode(dict_obj)
    else:
        if where == "from_project":
            return gazu.shot.all_sequences_for_project(dict_obj)
        return gazu.shot.all_sequences_for_episode(dict_obj)


def GetSequenceByName(project_dict, seq_name, episode_dict=None):
    return gazu.shot.get_sequence_by_name(project_dict, seq_name, episode_dict)


def RemoveSequence(sequence_dict):
    return gazu.shot.remove_sequence(sequence_dict)


def GetShots(dict_obj, where="from_sequence", user=False, getCanceled=False):
    if user:
        if where == "from_sequence":
            shots = gazu.user.all_shots_for_sequence(dict_obj)
            for shot in shots:
                shot.update({"sequence_name": dict_obj["name"]})
        else:
            shots = gazu.user.all_shots_for_project(dict_obj)
    else:
        if where == "from_sequence":
            shots = gazu.shot.all_shots_for_sequence(dict_obj)
        else:
            shots = gazu.shot.all_shots_for_project(dict_obj)
    return shots


def GetShotByName(sequence_dict, shot_name):
    return gazu.shot.get_shot_by_name(sequence_dict, shot_name)


def RemoveShot(shot_dict):
    return gazu.shot.remove_shot(shot_dict)


def GetAssets(proj_dict, asset_type, user=False, getCanceled=False):
    if user:
        return gazu.user.all_assets_for_asset_type_and_project(proj_dict, asset_type)
    return gazu.asset.all_assets_for_project_and_type(proj_dict, asset_type)


def GetAssetByName(proj_dict, asset_name):
    return gazu.asset.get_asset_by_name(proj_dict, asset_name)


def RemoveAsset(asset_dict):
    return gazu.asset.remove_asset(asset_dict)


def GetAssetType(asset_type_id, user=False):
    return gazu.asset.get_asset_type(asset_type_id)


def RemoveAssetType(asset_type_dict):
    return gazu.asset.remove_asset_type(asset_type_dict)


def GetAssetTypes():
    return gazu.asset.all_asset_types()


def GetEntity(id):
    return gazu.entity.get_entity(id)


def GetEpisodeName(ep_id):
    return gazu.entity.get_entity(ep_id)["name"]


def GetTasksForAsset(asset_dict):
    return gazu.task.all_tasks_for_asset(asset_dict)


def GetTasksForShot(shot_dict):
    return gazu.task.all_tasks_for_shot(shot_dict)


def _getInfoFolderPath(core, folder_name):
    base_dir = os.path.dirname(getattr(core, "prismIni", "") or "")
    if not base_dir and hasattr(core, "projectPath"):
        base_dir = os.path.join(core.projectPath, "00_Pipeline")
    return os.path.join(base_dir, folder_name)


def DownloadThumbnail(self, name, preview_file_id, folder_name, entity=None):
    local_preview_id = self.core.getConfig(
        name, "thumbnailID", config=folder_name.lower()
    )

    if preview_file_id != local_preview_id:
        info_dir = _getInfoFolderPath(self.core, folder_name)
        previewImgPath = os.path.join(info_dir, "%s_preview" % name)

        if preview_file_id is None or preview_file_id == "":
            if os.path.isfile(previewImgPath + ".jpg"):
                try:
                    os.remove(previewImgPath + ".jpg")
                except Exception:
                    pass
            return "", False, True

        file_exists = os.path.exists(previewImgPath + ".jpg")
        if file_exists is False or preview_file_id != local_preview_id:
            preview_info = gazu.files.get_preview_file(preview_file_id)
            extension = preview_info.get("extension") or "jpg"
            thumbnailPath = previewImgPath + "." + extension
            mkdir_p(info_dir)
            gazu.files.download_preview_file_thumbnail(
                preview_file_id, thumbnailPath
            )
            if os.path.splitext(thumbnailPath)[1].lower() != ".jpg":
                pixmap = self.core.media.getPixmapFromPath(thumbnailPath)
                self.core.media.savePixmap(pixmap, previewImgPath + ".jpg")
                try:
                    os.remove(thumbnailPath)
                except Exception:
                    pass

            # Đồng bộ vào hệ thống preview của Prism 2 nếu có hàm setEntityPreview
            if entity and hasattr(self.core.entities, "setEntityPreview"):
                jpg_path = previewImgPath + ".jpg"
                if os.path.isfile(jpg_path):
                    pmap = self.core.media.getPixmapFromPath(jpg_path)
                    if pmap:
                        try:
                            self.core.entities.setEntityPreview(
                                entity, pmap
                            )
                        except Exception:
                            pass

        if file_exists:
            return preview_file_id, False, True
        else:
            return preview_file_id, True, False

    return False, False, False


def createKitsuEpisode(project_dict, episode_name):
    if episode_name is None:
        return None, False

    episode_dict = gazu.shot.get_episode_by_name(project_dict, episode_name)
    if episode_dict is None:
        episode_dict = gazu.shot.new_episode(project_dict, episode_name)
        return episode_dict, True
    return episode_dict, False


def createKitsuSequence(project_dict, sequence_name, episode_dict=None):
    if episode_dict is None:
        sequence_dict = gazu.shot.get_sequence_by_name(
            project_dict, sequence_name
        )
    else:
        sequence_dict = gazu.shot.get_sequence_by_name(
            project_dict, sequence_name, episode_dict
        )

    if sequence_dict is None:
        if episode_dict is None:
            sequence_dict = gazu.shot.new_sequence(project_dict, sequence_name)
        else:
            sequence_dict = gazu.shot.new_sequence(
                project_dict, sequence_name, episode_dict
            )
        return sequence_dict, True
    return sequence_dict, False


def createKitsuShot(project_dict, sequence_dict, shot_name, ranges):
    shot_dict = gazu.shot.get_shot_by_name(sequence_dict, shot_name)

    if shot_dict is None:
        if ranges is not None and len(ranges) == 2 and ranges[0] is not None and ranges[1] is not None:
            f_in = int(ranges[0])
            f_out = int(ranges[1])
            shot_dict = gazu.shot.new_shot(
                project=project_dict,
                sequence=sequence_dict,
                name=shot_name,
                nb_frames=(f_out - f_in + 1),
                frame_in=f_in,
                frame_out=f_out,
                data={},
            )
        else:
            shot_dict = gazu.shot.new_shot(
                project=project_dict,
                sequence=sequence_dict,
                name=shot_name,
                data={},
            )
        return shot_dict, True
    return shot_dict, False


def createKitsuAssetType(name):
    if not name:
        name = "General"
    asset_type_dict = gazu.asset.get_asset_type_by_name(name)
    if asset_type_dict is None:
        asset_type_dict = gazu.asset.new_asset_type(name)
        return asset_type_dict, True
    return asset_type_dict, False


def createKitsuAsset(
    project_dict,
    asset_type_dict,
    asset_name,
    asset_description,
    extra_data=None,
    episode=None,
):
    if extra_data is None:
        extra_data = {}
    asset_dict = gazu.asset.get_asset_by_name(project_dict, asset_name)

    if asset_dict is None:
        asset_dict = gazu.asset.new_asset(
            project_dict,
            asset_type_dict,
            asset_name,
            asset_description,
            extra_data,
            episode,
        )
        return asset_dict, True
    return asset_dict, False


def createKitsuTask(entity_dict, task_type):
    if entity_dict and task_type:
        return gazu.task.new_task(entity_dict, task_type)
    return None


def uploadThumbnail(entity_id, thumbnail_URL, task_type_dict, user_Email):
    uploadRevision(
        entity_id, thumbnail_URL, task_type_dict, None, user_Email, True
    )
    entity_dict = gazu.entity.get_entity(entity_id)
    return entity_dict.get("preview_file_id")


def uploadRevision(
    entity_id,
    thumbnail_URL,
    task_type_dict,
    type_status_dict,
    user_Email,
    set_preview,
    comment="",
):
    entity_dict = gazu.entity.get_entity(entity_id)
    person_dict = (
        gazu.person.get_person_by_email(user_Email) if user_Email else None
    )
    task_dict = gazu.task.get_task_by_name(entity_dict, task_type_dict)
    if task_dict is None:
        task_dict = gazu.task.new_task(entity_dict, task_type_dict)

    if type_status_dict is None:
        type_status_dict = gazu.task.get_task_status(task_dict)

    comment_dict = addComment(
        task_dict,
        type_status_dict,
        comment=comment,
        person=person_dict,
    )

    preview_dict = gazu.task.add_preview(
        task_dict, comment_dict, thumbnail_URL
    )

    if set_preview is True:
        gazu.task.set_main_preview(preview_dict)

    return preview_dict


def addComment(task, task_status="todo", comment="", person=None):
    if not isinstance(task_status, dict):
        if task_status is None:
            task_status = "todo"
        task_status = gazu.task.get_task_status_by_short_name(task_status)

    # Vá lỗi gọi get_person_by_email 2 lần khi person đã là dict
    if isinstance(person, str):
        person = gazu.person.get_person_by_email(person)

    return gazu.task.add_comment(task, task_status, comment, person)


def getTaskTypes(entity_dict=None):
    if entity_dict is None:
        return gazu.task.all_task_types()

    e_type = entity_dict.get("type")
    if e_type == "Episode":
        return gazu.task.all_task_types_for_episode(entity_dict)
    elif e_type == "Sequence":
        return gazu.task.all_task_types_for_sequence(entity_dict)
    elif e_type == "Scene":
        return gazu.task.all_task_types_for_scene(entity_dict)
    elif e_type == "Shot":
        return gazu.task.all_task_types_for_shot(entity_dict)
    elif e_type == "Asset":
        return gazu.task.all_task_types_for_asset(entity_dict)
    return gazu.task.all_task_types()


def doEntityExist(entity_id):
    if not entity_id:
        return False
    try:
        return gazu.entity.get_entity(entity_id) is not None
    except Exception:
        return False
