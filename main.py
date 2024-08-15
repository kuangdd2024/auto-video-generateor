import sys

if len(sys.argv) == 1:
    from auto_video_generateor.free_webui import demo
elif sys.argv[1] == ["1", "simple"]:
    from auto_video_generateor.simple_webui import demo
elif sys.argv[1] == ["2", "qianfan"]:
    from auto_video_generateor.qianfan_based_webui import demo
elif sys.argv[1] == ["3", "free"]:
    from auto_video_generateor.free_webui import demo
else:
    assert sys.argv[1] in '123'

if __name__ == "__main__":
    demo.launch(server_name='127.0.0.1', server_port=8000, show_error=True)
