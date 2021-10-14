

■ This script starts with checking if its "__name__" variable is indeed "__main__" to prevent unwanted execution if it is being imported to other codebase.

■ Then it executes "temp_open_close_all_docket_data_downloader" function with parameter provided for "open_docket" i.e crawling for open docket data is initiated first.

■ After being provided with open_docket base link, function "temp_open_close_all_docket_data_downloader" first checks if there is any file with pattern "open_docket*csv" in its root execution directory that has been created today or not if so then it simply returns false thus limiting only one crawl in a day.

■ If there aren't any file with pattern "open_docket*csv" in root directory that has been created today it proceeds further and calls function "available_search_result_page_links" with open_docket base link; this function returns list of all result pages link that can be browsed from base open docket page i.e it checks the page no of last page in search result and build links till first page with decrementing page no from last page. for ex- if last page link is :- https://www.gao.gov/legal/bid-protests/search?processed=1&closed=0&page=12

it'll build list of links like :-

https://www.gao.gov/legal/bid-protests/search?processed=1&closed=0&page=1
https://www.gao.gov/legal/bid-protests/search?processed=1&closed=0&page=2
https://www.gao.gov/legal/bid-protests/search?processed=1&closed=0&page=3
...
...
...
...
...
https://www.gao.gov/legal/bid-protests/search?processed=1&closed=0&page=12

■ Then it iterates over all resulted page links and checks first if the link is present in log file or not with function "log_file_presence_checker" if its there then it just skips that link.if not then it calls function "all_docket_data_from_search_page_link" with current search page link, this function returns list of dictionary containing open_docket data .Also writes a log in form of links as text that it has visited;

■ Function "all_docket_data_from_search_page_link" first grabs all available individual docket page link present on single given search page with help of function "docket_page_links_from_search_page" and then pass those links one by one throught function "extract_data_from_docket_page" and build a list of docket data dictionary and returns it. If "log_file_name_with_path" variable is present then it checks first if a link it is being passed to  "extract_data_from_docket_page" is present or not in log file, If not then only it pass that link for data extraction from docket page else skips it. Also after grabbing all docket data from search page it writes all those links to log file. This log file maintainence and checks helps in resuming if crawling interrupts midway due to some or other reason.

■ Function "extract_data_from_docket_page" takes single docket page link and returns dictionary of all docket information present on docket page while doing so it check if field value having "file number" doesn't have any anchor tag i.e with a "herf" link.if so then it passes those links to function "highlights_page_content_grabber", this function grabs decision highlights form highlights section block from page link and returns it as a string which later consumed by func "extract_data_from_docket_page" and returns all docket info in form of a dictionary.

■ Moving forward after grabbing all docket page information collected from from single search result page by function "temp_open_close_all_docket_data_downloader" in "data" variable it writes them all in "temp_file_name" which is generated in format of "(docket_type) + "_temp_data.json" where each line is json object containing data for each docket page.This process is repeated for each search page link i.e in current case from page 1- 12.

■ After successful execution of function "temp_open_close_all_docket_data_downloader" it just returns "temp_file_name" which is later consumed by function "final_csv_generator"

■ Function "final_csv_generator" reads "temp_file_name" which is generated in format of "(docket_type) + "_temp_data.json" line by line and then convert it in to a csv file with file name having current date and docket type, then it deletes current log file and temp file as they are no longer necessary as final crawled csv file for open docket data is already generated. 


■ This might be a good question as why temp json file is created and why not directly data is written to a csv file, well the problem with csv is you can't have flactuating header i.e no of information available on docket page can change and indeed it gets increase/decrease on our use case, having first temprary json file helps us from losing any new available data and prevents from hardcoding keys, list of Flat Json are perfect for creatind a csv .
■ Then time taken to complete open docket crawl is returned and if it's less than 5 sec then probably executor function alrady skipped everything and checked todays file alredy being crawled and returns the message.
■Similarly above steps are repeated again for closed_docket with its base link



