import argparse
import logging
import os
import pprint
from collections import Counter
from pathlib import Path

from .pathmatcher import PathMatcher
from .pathmatcher import TRACE_TYPES
from .utils import load_config

logger = logging.getLogger(__name__)


def get_args():
    """
    Parse command line arguments
    """
    descr = ""
    usage = "python -m mps_sql <path to folder> <path to config file> [OPTIONS]"
    parser = argparse.ArgumentParser(description=descr, usage=usage)
    parser.add_argument(
        action="store",
        dest="folder",
        type=str,
        help="Path to the root folder",
    )
    parser.add_argument(
        action="store",
        dest="config",
        type=str,
        help="Path to the config file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="More printing",
    )
    parser.add_argument(
        "-nc",
        "--no-check",
        dest="no_check",
        action="store_true",
        help="Check that everthing is parsed correctly",
    )
    parser.add_argument(
        "-a",
        "--add-data",
        dest="add_data",
        action="store_true",
        help="Add data to the database",
    )

    return parser


def check_args(args):
    """Check whether the folder and config given as arguments exist

    Raises:
        ValueError: The folder or config name given does not exist, or is not
            a directory/file.
    """
    folder = Path(args["folder"])
    config = Path(args["config"])

    if not folder.exists():
        raise ValueError("the given folder does not exist")
    if not folder.is_dir():
        raise ValueError("the given folder is not a directory")
    if not config.is_file():
        raise ValueError("the given config is not a file")

    args["folder"] = folder
    args["config"] = config

    if args["verbose"]:
        from . import set_log_level

        set_log_level(logging.DEBUG)

    return True


def check(args):  # noqa: C901

    logger.info(f"Checking folder {args['folder']} with config {args['config']}")
    config = load_config(args["config"])
    pathmatcher = PathMatcher(config, root=args["folder"])
    exclude = config.get("exclude", [])

    num_files = 0

    cnt_keys = config.get("unique_columns", [])

    counters = {k: Counter() for k in cnt_keys}
    datas = {}
    for root, dirs, files in os.walk(args["folder"]):
        for f in files:
            path = Path(root).joinpath(f)

            skip = False
            for ex in exclude:
                if ex in path.as_posix():
                    skip = True
                    break
            if skip:
                continue

            if path.suffix in [".nd2", ".czi"]:
                logger.debug(path)
                try:
                    mps_data = pathmatcher(path)
                except RuntimeError as err:
                    logging.error(err)
                    return

                # data = mps_data.sql_data()
                data = mps_data.to_dict()
                logger.debug(data)
                num_files += 1
                for k in cnt_keys:
                    counters[k][data.get(k)] += 1

                try:
                    unique_key = "_".join(data[k] for k in cnt_keys)
                except KeyError as ex:
                    logger.info(f"Failed to get info from path {path}")
                    logger.info(ex, exc_info=True)
                    continue

                if unique_key not in datas:
                    datas[unique_key] = {}
                if "trace_type" not in data:
                    raise ValueError(
                        f"Could not find trace type for output \n{pprint.pformat(data)}",
                    )

                if data["trace_type"] in datas[unique_key]:
                    msg = (
                        f"Duplicatee trace for trace type {data['trace_type']} "
                        f"and key {unique_key}. The following paths have the same unique key: "
                        f"\n{datas[unique_key][data['trace_type']]}"
                        f"\n{path}"
                    )
                    if data["trace_type"] == "brightfield":
                        # This is typically because they also take a picture
                        logger.debug(msg)
                    else:
                        logger.warning(msg)
                datas[unique_key][data["trace_type"]] = path

    cor_traces = {k: list(d.keys()) for k, d in datas.items()}
    for trace_type in TRACE_TYPES:
        for experiment, types in cor_traces.items():
            if trace_type not in types:
                logger.info(
                    f"Missing trace type '{trace_type}' for experiment: {experiment}",
                )

    msg = ""
    for key, cnt in counters.items():
        if len(cnt) == 1 and None in cnt:
            continue
        msg += f"\nKey: {key} \n {cnt}"
    logger.info(f"\nDone checking - found {num_files} files \n{msg}")


def main():
    args = vars(get_args().parse_args())

    try:
        check_args(args)
    except ValueError as err:
        logger.error(err)
        return

    if not args["no_check"]:
        check(args)
