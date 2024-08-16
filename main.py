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

demo.queue(max_size=1022).launch(
    server_name="0.0.0.0",
    inbrowser=True,
    share=True,
    server_port=8000,
    quiet=True,
    # auth=lambda x, y: x == y,  # ("admin", "pass1234"),
    # auth_message='欢迎来到自动视频生成的世界'
)
