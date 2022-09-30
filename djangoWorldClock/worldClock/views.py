from django.shortcuts import render, redirect
import requests
from loguru import logger
import sys
from logtail import LogtailHandler

logtail_handler = LogtailHandler(source_token="<logtail source token>")

logger.remove(0)

logger.add(
    sys.stderr,
    format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {message} | {extra}",
    level="TRACE",
    backtrace=False,
    diagnose=False,
)

logger.add(
    logtail_handler,
    format="{message}",
    level="INFO",
    backtrace=False,
    diagnose=False,
)

# Create your views here.
def home(request):
    logger.trace("visit to homepage")

    return render(request, "home.html")


def search(request):
    # If the request method is not POST, redirect to the home page
    if request.method != "POST":
        logger.info(
            "redirecting '{method}' request to '{path}' to '/'",
            method=request.method,
            path=request.path,
        )
        return redirect("/")

    # Get the search query
    query = request.POST.get("q", "").strip()

    if not query:
        logger.info("search query is empty. Redirecting to /")
        return redirect("/")

    searchLogger = logger.bind(query=query)

    searchLogger.info("incoming search query for '{query}'", query=query)

    try:
        # Pass the search query to the Nominatim API to get a location
        location = requests.get(
            "https://nominatim.openstreetmap.org/search",
            {"q": query, "format": "json", "limit": "1"},
        ).json()

        searchLogger.bind(location=location).debug("Nominatim API response")

        # If a location is found, pass the coordinate to the Time API to get the current time
        if location:
            coordinate = [location[0]["lat"], location[0]["lon"]]

            time = requests.get(
                "https://timeapi.io/api/Time/current/coordinate",
                {"latitude": coordinate[0], "longitude": coordinate[1]},
            )

            searchLogger.bind(time=time).debug("Time API response")

            searchLogger.bind(coordinate=coordinate).trace(
                "Search query '{query}' succeeded without errors"
            )

            return render(
                request, "success.html", {"location": location[0], "time": time.json()}
            )

        # If a location is NOT found, return the error page
        else:
            searchLogger.info("location '{query}' not found", query=query)
            return render(request, "fail.html")
    except Exception as error:
        searchLogger.exception(error)
        return render(request, "500.html")
