import base64
from PySide6.QtCore import QBuffer, QIODevice

def image_as_base64(image):
    # Resize large screenshots to control context/memory use.
    if image.width() > 1600 or image.height() > 1600:
        image = image.scaled(1600, 1600, __import__('PySide6.QtCore',fromlist=['Qt']).Qt.AspectRatioMode.KeepAspectRatio)
    data = QBuffer()
    data.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(data, 'PNG'):
        raise ValueError('Could not encode screenshot')
    return base64.b64encode(bytes(data.data())).decode('ascii')
