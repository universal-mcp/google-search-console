import urllib.parse
from typing import Any, Optional, List, Dict # Changed from dict to Dict for older Pythons, but dict is fine for 3.9+

from universal_mcp.applications import APIApplication
from universal_mcp.integrations import Integration
import logging
import httpx

logger = logging.getLogger(__name__)


class GoogleSearchConsoleApp(APIApplication):
    def __init__(self, integration: Integration = None, **kwargs) -> None:
        super().__init__(name='google-search-console', integration=integration, **kwargs)
        self.webmasters_base_url = "https://www.googleapis.com/webmasters/v3"
        self.searchconsole_base_url = "https://searchconsole.googleapis.com/v1"

    def _get_headers(self) -> Dict[str, str]:
      """
      Override the base method to return empty headers.
      The Gemini API key is passed as a query parameter ('key'),
      not in an Authorization header for these endpoints.
      """
      logger.debug(f"Overriding _get_headers for {self.name}. Returning empty dict to prevent default auth header.")
      return {}

    def _add_api_key_param(self, params: Dict[str, Any] | None) -> Dict[str, Any]:
        """Helper to add the API key as a 'key' query parameter."""
        actual_params = params.copy() if params else {}
        if 'key' not in actual_params and self.integration:
            try:
                credentials = self.integration.get_credentials()
                api_key = credentials.get("api_key")
                if api_key:
                    actual_params['key'] = api_key
                    logger.debug("Added API key as query parameter.")
                else:
                      # This might happen if the store returned credentials without an api_key field
                    logger.warning("API key retrieved from integration credentials is None or empty.")
            except Exception as e:
                logger.error(f"Error retrieving API key from integration: {e}")
        return actual_params

    def _get(self, url: str, params: Dict[str, Any] | None = None) -> httpx.Response:
        """
        Make a GET request, ensuring the API key is added as a query parameter.
        """
        actual_params = self._add_api_key_param(params)
        logger.debug(f"Making GET request to {url} with params: {actual_params}")
        return super()._get(url, params=actual_params)

    def _post(
        self, url: str, data: Dict[str, Any], params: Dict[str, Any] | None = None
    ) -> httpx.Response:
        """
        Make a POST request, ensuring the API key is added as a query parameter.
        """
        actual_params = self._add_api_key_param(params)
        logger.debug(
            f"Making POST request to {url} with params: {actual_params} and data: {data}"
        )
        # Note: The parent _post in application.py still uses httpx.post directly
        # and calls self._get_headers() again, which is fine because our override returns {}.
        return super()._post(url, data=data, params=actual_params)

    def _put(
        self, url: str, data: dict[str, Any], params: dict[str, Any] | None = None
    ) -> httpx.Response:
        """
        Make a PUT request to the specified URL.

        Args:
            url: The URL to send the request to
            data: The data to send in the request body
            params: Optional query parameters

        Returns:
            httpx.Response: The response from the server

        Raises:
            httpx.HTTPError: If the request fails
        """
        actual_params = self._add_api_key_param(params)
        logger.debug(
            f"Making PUT request to {url} with params: {actual_params} and data: {data}"
        )
        return super()._post(url, data=data, params=actual_params)
    
    
    def _delete(self, url: str, params: Dict[str, Any] | None = None) -> httpx.Response:
        """
        Make a DELETE request, ensuring the API key is added as a query parameter.
        """
        actual_params = self._add_api_key_param(params)
        logger.debug(f"Making DELETE request to {url} with params: {actual_params}")
        return super()._delete(url, params=actual_params)

    def delete_sitemap(self, siteUrl: str, feedpath: str) -> None:
        """
        Deletes a sitemap from this site. Typically returns HTTP 204 No Content on success.

        Args:
            siteUrl (str): The site's URL, including protocol (e.g. 'http://www.example.com/').
            feedpath (str): The URL of the sitemap to delete. Example: 'http://www.example.com/sitemap.xml'.

        Returns:
            None: If the request is successful.
        
        Tags:
            sitemap_management
        """
        # Encode URL parts used as path segments
        siteUrl_encoded = urllib.parse.quote(siteUrl, safe='')
        feedpath_encoded = urllib.parse.quote(feedpath, safe='')
        
        url = f"{self.webmasters_base_url}/sites/{siteUrl_encoded}/sitemaps/{feedpath_encoded}"
        response = self._delete(url)
        response.raise_for_status()
        return None

    def get_sitemap(self, siteUrl: str, feedpath: str) -> Dict[str, Any]:
        """
        Retrieves information about a specific sitemap.

        Args:
            siteUrl (str): The site's URL, including protocol (e.g. 'http://www.example.com/').
            feedpath (str): The URL of the sitemap to retrieve. Example: 'http://www.example.com/sitemap.xml'.

        Returns:
            Dict[str, Any]: Sitemap resource.
            
        Tags:
            sitemap_management
        """
        siteUrl_encoded = urllib.parse.quote(siteUrl, safe='')
        feedpath_encoded = urllib.parse.quote(feedpath, safe='')

        url = f"{self.webmasters_base_url}/sites/{siteUrl_encoded}/sitemaps/{feedpath_encoded}"
        response = self._get(url)
        response.raise_for_status()
        return response.json()

    def list_sitemaps(self, siteUrl: str, sitemapIndex: Optional[str] = None) -> Dict[str, Any]:
        """
        Lists the sitemaps-entries submitted for this site, or included in the sitemap index file 
        (if sitemapIndex is specified in the request).

        Args:
            siteUrl (str): The site's URL, including protocol (e.g. 'http://www.example.com/').
            sitemapIndex (Optional[str]): The URL of the sitemap index. 
                                          Example: 'http://www.example.com/sitemap_index.xml'.

        Returns:
            Dict[str, Any]: List of sitemap resources.
            
        Tags:
            sitemap_management
        """
        siteUrl_encoded = urllib.parse.quote(siteUrl, safe='')
        url = f"{self.webmasters_base_url}/sites/{siteUrl_encoded}/sitemaps"
        
        query_params = {}
        if sitemapIndex is not None:
            query_params['sitemapIndex'] = sitemapIndex
        
        response = self._get(url, params=query_params if query_params else None)
        response.raise_for_status()
        return response.json()

    def submit_sitemap(self, siteUrl: str, feedpath: str) -> None:
        """
        Submits a sitemap for a site. Typically returns HTTP 204 No Content on success.

        Args:
            siteUrl (str): The site's URL, including protocol (e.g. 'http://www.example.com/').
            feedpath (str): The URL of the sitemap to submit. Example: 'http://www.example.com/sitemap.xml'.

        Returns:
            None: If the request is successful.
            
        Tags:
            sitemap_management
        """
        siteUrl_encoded = urllib.parse.quote(siteUrl, safe='')
        feedpath_encoded = urllib.parse.quote(feedpath, safe='')

        url = f"{self.webmasters_base_url}/sites/{siteUrl_encoded}/sitemaps/{feedpath_encoded}"
        # PUT requests for submitting/notifying often don't have a body.
        response = self._put(url, data=None) 
        response.raise_for_status()
        return None

    # --- Sites ---

    def add_site(self, siteUrl: str) -> Dict[str, Any]:
        """
        Adds a site to the set of the user's sites in Search Console.
        This will require verification of the site ownership.
        If successful, this method returns a site resource in the response body.

        Args:
            siteUrl (str): The URL of the site to add. Example: 'http://www.example.com/'.

        Returns:
            Dict[str, Any]: Site resource upon successful addition.
            
        Tags:
            site_management
        """
        siteUrl_encoded = urllib.parse.quote(siteUrl, safe='')
        url = f"{self.webmasters_base_url}/sites/{siteUrl_encoded}"
        # This specific PUT for adding a site generally does not require a body;
        # the resource identifier is the siteUrl itself.
        # Google API docs state it returns a site resource.
        response = self._put(url, data=None)
        response.raise_for_status()
        return response.json()

    def delete_site(self, siteUrl: str) -> None:
        """
        Removes a site from the set of the user's Search Console sites.
        Typically returns HTTP 204 No Content on success.

        Args:
            siteUrl (str): The URL of the site to delete. Example: 'http://www.example.com/'.

        Returns:
            None: If the request is successful.
            
        Tags:
            site_management
        """
        siteUrl_encoded = urllib.parse.quote(siteUrl, safe='')
        url = f"{self.webmasters_base_url}/sites/{siteUrl_encoded}"
        response = self._delete(url)
        response.raise_for_status()
        return None

    def get_site(self, siteUrl: str) -> Dict[str, Any]:
        """
        Retrieves information about a specific site.

        Args:
            siteUrl (str): The site's URL, including protocol (e.g. 'http://www.example.com/').

        Returns:
            Dict[str, Any]: Site resource.
            
        Tags:
            site_management
        """
        siteUrl_encoded = urllib.parse.quote(siteUrl, safe='')
        url = f"{self.webmasters_base_url}/sites/{siteUrl_encoded}"
        response = self._get(url)
        response.raise_for_status()
        return response.json()

    def list_sites(self) -> Dict[str, Any]:
        """
        Lists the user's Search Console sites.

        Returns:
            Dict[str, Any]: List of site resources.
            
        Tags:
            site_management
        """
        url = f"{self.webmasters_base_url}/sites"
        response = self._get(url)
        response.raise_for_status()
        return response.json()

    # --- URL Inspection ---

    def index_inspect_url(self, inspectionUrl: str, siteUrl: str, languageCode: Optional[str] = None) -> Dict[str, Any]:
        """
        Inspects a URL in Google Index and provides information about its status.

        Args:
            inspectionUrl (str): The URL to inspect. Example: 'https://www.example.com/mypage'.
            siteUrl (str): The site URL (property) to inspect the URL under. 
                           Must be a property in Search Console. Example: 'sc-domain:example.com' or 'https://www.example.com/'.
            languageCode (Optional[str]): Optional. The BCP-47 language code for the inspection. Example: 'en-US'.

        Returns:
            Dict[str, Any]: Inspection result containing details about the URL's indexing status.
            
        Tags:
            url_inspection, indexing
        """
        url = f"{self.searchconsole_base_url}/urlInspection/index:inspect"
        request_body: Dict[str, Any] = {
            'inspectionUrl': inspectionUrl,
            'siteUrl': siteUrl,
        }
        if languageCode is not None:
            request_body['languageCode'] = languageCode
        
        # Assuming _post handles dict as JSON payload, similar to ExaApp
        response = self._post(url, data=request_body) 
        response.raise_for_status()
        return response.json()

    # ... (previous methods of GoogleSearchConsoleApp) ...

    def query_search_analytics(
        self,
        siteUrl: str,
        startDate: str,
        endDate: str,
        dimensions: Optional[List[str]] = None,
        dimensionFilterGroups: Optional[List[Dict[str, Any]]] = None,
        aggregationType: Optional[str] = None,
        rowLimit: Optional[int] = None,
        startRow: Optional[int] = None,
        dataState: Optional[str] = None,
        search_type: Optional[str] = None  # 'type' is a reserved keyword in Python
    ) -> Dict[str, Any]:
        """
        Queries your search traffic data with filters and parameters that you define.
        The method returns zero or more rows grouped by the row that you define.
        You must define a date range of one or more days.

        Args:
            siteUrl (str): The site's URL, including protocol (e.g. 'http://www.example.com/').
            startDate (str): Start date of the requested period in YYYY-MM-DD format.
            endDate (str): End date of the requested period in YYYY-MM-DD format.
            dimensions (Optional[List[str]]): List of dimensions to group the data by.
                Possible values: "date", "query", "page", "country", "device", "searchAppearance".
                Example: ["date", "query"].
            dimensionFilterGroups (Optional[List[Dict[str, Any]]]): Filter the results by dimensions.
                Example: [{
                    "groupType": "and",
                    "filters": [{
                        "dimension": "country",
                        "operator": "equals",
                        "expression": "USA"
                    }, {
                        "dimension": "device",
                        "operator": "equals",
                        "expression": "DESKTOP"
                    }]
                }]
            aggregationType (Optional[str]): How data is aggregated.
                Possible values: "auto", "byPage", "byProperty". Default is "auto".
            rowLimit (Optional[int]): The maximum number of rows to return. Default is 1000. Max 25000.
            startRow (Optional[int]): Zero-based index of the first row to return. Default is 0.
            dataState (Optional[str]): Whether to filter for fresh data or all data.
                Possible values: "all", "final". Default "all".
            search_type (Optional[str]): Filter by search type.
                Example: "web", "image", "video", "news", "discover", "googleNews".
                This corresponds to the 'type' parameter in the API.

        Returns:
            Dict[str, Any]: Search analytics data.
            
        Tags:
            search_analytics, reporting
        """
        siteUrl_encoded = urllib.parse.quote(siteUrl, safe='')
        url = f"{self.webmasters_base_url}/sites/{siteUrl_encoded}/searchAnalytics/query"

        request_body: Dict[str, Any] = {
            'startDate': startDate,
            'endDate': endDate,
        }
        if dimensions is not None:
            request_body['dimensions'] = dimensions
        if dimensionFilterGroups is not None:
            request_body['dimensionFilterGroups'] = dimensionFilterGroups
        if aggregationType is not None:
            request_body['aggregationType'] = aggregationType
        if rowLimit is not None:
            request_body['rowLimit'] = rowLimit
        if startRow is not None:
            request_body['startRow'] = startRow
        if dataState is not None:
            request_body['dataState'] = dataState
        if search_type is not None:
            request_body['type'] = search_type # API expects 'type'

        response = self._post(url, data=request_body)
        response.raise_for_status()
        return response.json()

    def list_tools(self):
        return [
            self.delete_sitemap,
            self.get_sitemap,
            self.list_sitemaps,
            self.submit_sitemap,
            self.add_site,
            self.delete_site,
            self.get_site,
            self.list_sites,
            self.index_inspect_url,
            self.query_search_analytics,
        ]