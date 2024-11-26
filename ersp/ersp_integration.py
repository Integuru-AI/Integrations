import aiohttp
import certifi
from typing import Dict, Any, Union
from bs4.element import Tag
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import date, timedelta, datetime

from helpers.classes.network_requester import NetworkRequester
from submodule_integrations.models.integration import Integration
from submodule_integrations.utils.errors import IntegrationAuthError, IntegrationAPIError


class ErspIntegration(Integration):
    def __init__(self, user_agent: str = UserAgent().random):
        super().__init__("ersp")
        self.network_requester = None
        self.user_agent = user_agent
        self.url = "https://ck964.ersp.biz/index.cfm"

    async def initialize(self, network_requester: NetworkRequester = None):
        self.network_requester = network_requester

    async def _make_request(self, method: str, url: str, **kwargs) -> str:
        """
        Helper method to handle network requests using either custom requester or aiohttp
        """
        if self.network_requester:
            response = await self.network_requester.request(
                method, url, process_response=self._handle_response, **kwargs
            )
            return response
        else:
            async with aiohttp.ClientSession() as session:
                # TODO: fix ssl error and enable ssl checking
                async with session.request(method, url, ssl=False, **kwargs) as response:
                    return await self._handle_response(response)

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Union[str, Any]:
        if response.status == 200:
            return await response.text()

        status_code = response.status
        # do things with fail status codes
        if 400 <= status_code < 500:
            # potential auth caused
            reason = response.reason
            raise IntegrationAuthError(
                f"ESRP: {status_code} - {reason} \n{await response.text()}"
            )
        elif status_code == 302:
            # should rarely happen as redirects should be automatic
            raise IntegrationAPIError(
                self.integration_name,
                f"forced redirection caught to {response.url}. \n{await response.text()}"
            )
        else:
            raise IntegrationAPIError(
                self.integration_name,
                f"ESRP: {status_code} - {response.headers}",
                status_code,
            )

    def _setup_headers(self) -> dict:
        # prep headers and params for actual report request
        _headers = {
            'Host': 'ck964.ersp.biz',
            'User-Agent': self.user_agent,
            'Accept': 'text/html',
        }

        return _headers

    @staticmethod
    def _get_date_and_week_start():
        """
        Get today's date and week start and format properly for params.
        """
        current_date = date.today()
        formatted_date = current_date.strftime("%m/%d/%Y")

        days_to_monday = current_date.weekday()
        first_day_of_week = current_date - timedelta(days=days_to_monday)
        first_day_of_week_formatted = first_day_of_week.strftime("%m/%d/%Y")

        return formatted_date, first_day_of_week_formatted

    @staticmethod
    def _get_current_year_month_quarter():
        """
        Returns the current year, month number, and quarter.

        Returns:
            tuple: A tuple containing the current year (int), month number (int), and quarter (int).
        """
        current_date = datetime.now()

        # Extract the current year and month
        current_year = current_date.year
        current_month = current_date.month

        if current_month in [1, 2, 3]:
            current_quarter = 1
        elif current_month in [4, 5, 6]:
            current_quarter = 2
        elif current_month in [7, 8, 9]:
            current_quarter = 3
        else:
            current_quarter = 4

        return current_year, current_month, current_quarter

    @staticmethod
    def _parse_table_rows_to_list(table: Tag, include_blank_rows: bool = False):
        """
        Parse an HTML table into a list of dictionaries, with consistent column headers and empty cell handling.
        Empty cells are represented as empty strings. For rows with fewer cells than headers, remaining cells
        are filled with empty strings.

        Args:
            table (Tag): BeautifulSoup Tag object containing the HTML table to parse
            include_blank_rows (bool): Whether to include rows where all cells are empty. Defaults to False.

        Returns:
            list[dict]: List of dictionaries where each dictionary represents a row.
                       Keys are column headers, values are cell contents.
                       Empty cells are represented as empty strings ("").
        """

        headers = []
        header_row = table.find('tr')
        if header_row:
            # Try to find th elements first
            th_cells = header_row.find_all('th')
            if th_cells:
                headers = [th.text.strip() for th in th_cells]
            else:
                # If no th elements, use td elements
                headers = [td.text.strip() for td in header_row.find_all('td')]

        # If still no headers, create generic column names
        if not headers:
            # Find the row with maximum number of columns
            max_cols = max(len(row.find_all(['td', 'th'])) for row in table.find_all('tr'))
            headers = [f'Column_{i + 1}' for i in range(max_cols)]

        # Patch for headers with improper \n that causes header texts to break
        if any('\n' in header for header in headers):
            headers = [header.split('\n')[0] for header in headers]

        empty_value = ""
        rows = []
        for tr in table.find_all('tr')[1:]:  # Skip header row
            row_data = {}
            cells = tr.find_all('td')

            # Check if row has any non-empty cells
            has_data = any(cell.text.strip() for cell in cells)

            if has_data or include_blank_rows:
                for i, header in enumerate(headers):
                    if i < len(cells):
                        cell_text = cells[i].text.strip()
                        row_data[header] = cell_text if cell_text else empty_value
                    else:
                        # If the row has fewer cells than headers, fill with empty_value
                        row_data[header] = empty_value

                rows.append(row_data)

        return rows

    async def fetch_comfort_keepers_report(self, cookies: dict = None):
        date_today = self._get_date_and_week_start()[0]
        params = {
            'event': 'admin.reports.resource.resourceData.viewResourceData',
            'statusFlag': 'A',
            'colNames': [
                'rFirst',
                'rLast',
                'rAddr1,rAddr2,rCity,rState,rZip',
                'rPhone',
                'rFax',
                'rMobile',
                'rGender',
                'hireDate',
                'rDOB',
                'rEmail',
            ],
            'administratorID': '',
            'administratorID_aNameDisplay': '-- All Administrators --',
            'adminShow': '0',
            'classID': '',
            'classID_classNameDisplay': '-- Select Class --',
            'tagSelect_select': '',
            'tagSelect': '',
            'tagOption': 'ANY',
            'sortBy': 'last',
            'excel': 'N',
            'dateFilterOption': 'OR',
            'dateFilterBy': 'rDOB',
            'dateFilterBy_from': date_today,
            '__dateFilterBy_from_hidden': date_today,
            'dateFilterBy_to': date_today,
            '__dateFilterBy_to_hidden': date_today,
            'resourceDataSubmit': [
                'Run Report',
                'Run Report',
            ],
        }

        headers = self._setup_headers()
        response = await self._make_request(method="GET", url=self.url, headers=headers, params=params, cookies=cookies)

        # Parse response html content into viable json data
        soup = BeautifulSoup(response, "html.parser")
        report_table_element = soup.select_one("table.functionLayout")

        comfort_keepers_list = self._parse_table_rows_to_list(report_table_element)
        return comfort_keepers_list

    async def fetch_activity_report(self, cookies: dict = None):
        date_today, date_monday = self._get_date_and_week_start()
        this_year, this_month, this_quarter = self._get_current_year_month_quarter()
        params = {
            'event': 'admin.reports.hours.activity.viewActivity',
            'comments': 'N',
            'reportType': 'LS',
            'summaryByCustomer': 'No',
            'SummaryPageBreaks': 'No',
            'ListSort': 'resource',
            'resourceID_inputmultiselect': 'Select Comfort Keeper(s)',
            'resourceID_rNameDisplay': '',
            'resShow': '0',
            'customerID_inputmultiselect': 'Select Customer(s)',
            'customerID_cNameDisplay': '',
            'custShow': '0',
            'administrator_inputmultiselect': 'Select Administrator(s)',
            'administrator_aNameDisplay': '',
            'adminShow': '0',
            'adminType': 'C',
            'customerClassIDs_inputmultiselect': 'Select Classes',
            'customerClassIDs_classNameDisplay': '',
            'filterAssign_AE_mins': '5',
            'filterAssign_AL_mins': '5',
            'filterAssign_DE_mins': '5',
            'filterAssign_DL_mins': '5',
            'ListType': 'D',
            'showTravelTime': '0',
            'showExpenses': 'N',
            'showComments': 'N',
            'showPayName': 'N',
            'showPayItem': 'N',
            'showTelephony': 'N',
            'showActions': 'N',
            'pagebreaks': 'N',
            'selectType': '0',
            'outputType': 'W',
            'date': date_today,
            '__date_hidden': date_today,
            'toDate': date_today,
            '__toDate_hidden': date_today,
            '__maxRange': '365',
            'searchWeek': date_monday,
            'Periodicity': 'M',
            'searchMonth': f'{this_month}',
            'MYear': f'{this_year}',
            'searchQuarter': f'{this_quarter}',
            'QYear': f'{this_year}',
            'searchYear': f'{this_year}',
        }
        headers = self._setup_headers()

        response = await self._make_request(method="GET", url=self.url, headers=headers, params=params, cookies=cookies)
        soup = BeautifulSoup(response, "html.parser")

        report_tables_processed = []
        report_tables = soup.select("table.functionLayout")
        for table in report_tables:
            first_row = table.select_one("tr")
            this_title = first_row.text.strip()  # the first row has the name of the comfort keeper, 2nd row is headers
            table.select_one("tr").decompose()

            table_data = self._parse_table_rows_to_list(table)
            report_tables_processed.append({this_title: table_data})

        return report_tables_processed

    async def fetch_calls_clocks_log(self, cookies: dict = None):
        date_today, date_monday = self._get_date_and_week_start()
        params = {
            'event': 'admin.reports.telephony.callLog.runCallLog',
            'resourceID_inputmultiselect': 'Select Comfort Keeper(s)',
            'resourceID_rNameDisplay': '',
            'resShow': '0',
            'customerID_inputmultiselect': 'Select Customer(s)',
            'customerID_cNameDisplay': '',
            'custShow': '0',
            'filterBy': '0',
            'clockType': '0',
            'date': date_today,
            '__date_hidden': date_today,
            'toDate': date_today,
            '__toDate_hidden': date_today,
            '__maxRange': '0',
            'Periodicity': 'W',
            'searchWeek': date_monday,
        }
        headers = self._setup_headers()
        response = await self._make_request(method="GET", url=self.url, headers=headers, params=params, cookies=cookies)

        soup = BeautifulSoup(response, "html.parser")
        unparsed_table = soup.select_one("table#callLogListing")
        calls_clocks_log_report = self._parse_table_rows_to_list(unparsed_table)

        return calls_clocks_log_report
