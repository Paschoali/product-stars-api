import datetime


def get_hours_in_seconds(hours):
    return datetime.timedelta(hours=hours).seconds


def is_json_content(request):
    return True if request.content_type == 'application/json' else False


def is_empty_content_length(request):
    return True if request and request.content_length and request.content_length <= 0 else False
