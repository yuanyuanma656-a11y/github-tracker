import argparse


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="GitHub 开源项目追踪与分析系统"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # add 命令
    add_parser = subparsers.add_parser(
        "add",
        help="添加并追踪一个 GitHub 仓库",
    )

    add_parser.add_argument(
        "--repo",
        required=True,
        help="GitHub 仓库，例如 psf/requests",
    )

    # update 命令
    subparsers.add_parser(
        "update",
        help="更新所有已经追踪的仓库",
    )

    # report 命令
    report_parser = subparsers.add_parser(
        "report",
        help="生成 GitHub 仓库分析报告",
    )

    report_parser.add_argument(
        "--repo",
        required=True,
        help="GitHub 仓库，例如 psf/requests",
    )

    return parser


def parse_args():
    """解析命令行参数。"""
    parser = create_parser()

    return parser.parse_args()