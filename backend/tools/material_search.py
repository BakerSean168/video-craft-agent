import os
from pathlib import Path
from core.schemas import VideoScript, UploadedMaterial, MaterialMatch


class MaterialSearcher:
    def __init__(self, library_dir: str | Path | None = None) -> None:
        if library_dir is None:
            backend_dir = Path(__file__).resolve().parents[1]
            project_dir = backend_dir.parent
            assets_path = project_dir / "assets" / "videos"
            asserts_path = project_dir / "asserts" / "videos"
            
            if assets_path.exists():
                self.library_dir = assets_path
            elif asserts_path.exists():
                self.library_dir = asserts_path
            else:
                self.library_dir = assets_path
        else:
            self.library_dir = Path(library_dir)

    def match_materials(
        self, script: VideoScript, uploads: list[UploadedMaterial]
    ) -> list[MaterialMatch]:
        matches = []
        
        # Get video files in library
        library_files = []
        if self.library_dir.exists() and self.library_dir.is_dir():
            library_files = [
                f for f in self.library_dir.iterdir()
                if f.is_file() and f.suffix.lower() in {".mp4", ".mov", ".avi", ".webm", ".mkv"}
            ]

        for scene in script.scenes:
            matched = False
            
            # 1. Match from uploads
            for upload in uploads:
                for kw in scene.visual_keywords:
                    if kw.lower() in upload.original_name.lower():
                        matches.append(
                            MaterialMatch(
                                scene_index=scene.index,
                                material_path=upload.local_path,
                                matched_keyword=kw,
                                source="uploaded",
                                fallback_used=False
                            )
                        )
                        matched = True
                        break
                if matched:
                    break
            
            if matched:
                continue

            # 2. Match from default library
            for lib_file in library_files:
                for kw in scene.visual_keywords:
                    if kw.lower() in lib_file.name.lower():
                        matches.append(
                            MaterialMatch(
                                scene_index=scene.index,
                                material_path=str(lib_file),
                                matched_keyword=kw,
                                source="library",
                                fallback_used=False
                            )
                        )
                        matched = True
                        break
                if matched:
                    break

            if matched:
                continue

            # 3. Fallback matching
            fallback_path = ""
            source = "fallback"
            
            default_file = self.library_dir / "default.mp4"
            if default_file.exists():
                fallback_path = str(default_file)
            elif library_files:
                fallback_path = str(library_files[0])
            elif uploads:
                fallback_path = uploads[0].local_path
                source = "uploaded"
            else:
                fallback_path = str(self.library_dir / "default.mp4")

            matches.append(
                MaterialMatch(
                    scene_index=scene.index,
                    material_path=fallback_path,
                    matched_keyword=None,
                    source=source,
                    fallback_used=True
                )
            )

        return matches


def match_materials(script: VideoScript, uploads: list[UploadedMaterial]) -> list[MaterialMatch]:
    searcher = MaterialSearcher()
    return searcher.match_materials(script, uploads)
