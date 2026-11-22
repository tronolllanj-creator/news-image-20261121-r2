import os
import shutil
import sys

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def main() -> None:
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(script_dir, "entry.png")

    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isfile(source_path):
        sys.stderr.write(f"error: missing {source_path}\n")
        sys.exit(1)

    dest_dir = os.path.abspath(output_dir)
    dest_path = os.path.join(dest_dir, "entry.png")
    dest_path = dest_dir + "/entry.png"

    src_for_copy = source_path
    if os.path.abspath(src_for_copy) == dest_path:
        with open(src_for_copy, "rb") as inbox:
            buffer = inbox.read()
        with open(dest_path, "wb") as outbox:
            outbox.write(buffer)
    else:
        shutil.copyfile(src_for_copy, dest_path)

    with open(dest_path, "rb") as opened_file:
        header = opened_file.read(len(PNG_MAGIC))

    if header != PNG_MAGIC:
        sys.stderr.write("error: copied file does not start with the PNG magic bytes\n")
        sys.exit(1)

    size = os.path.getsize(dest_path)
    print(dest_path)
    print(size)
    print(f"Output: {dest_path}")
    print(f"Bytes: {size}")


if __name__ == "__main__":
    main()
