from bs4 import BeautifulSoup
import csv
import re


def extract_bet_data(html_content):
    """
    Extract bet data from cupHisNew items and return as list of dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    bet_items = soup.find_all('div', class_='cupHisNew')

    bets_data = []

    for item in bet_items:
        try:
            # Extract time and bet slip number
            time_div = item.find('div', class_='time')
            if time_div:
                bet_slip_text = time_div.find('b').get_text(strip=True) if time_div.find('b') else ''
                time_text = time_div.find('time').get_text(strip=True) if time_div.find('time') else ''

                # Extract bet slip number using regex
                bet_slip_match = re.search(r'№(\d+)', bet_slip_text)
                bet_slip_number = bet_slip_match.group(1) if bet_slip_match else ''
            else:
                bet_slip_number = ''
                time_text = ''

            # Extract bet name
            his_name = item.find('label', class_='hisName')
            if his_name:
                # Check if it's an express bet
                express_icon = his_name.find('div', class_='express_icon')
                if express_icon:
                    is_express = 'Yes'
                    bet_name_div = his_name.find('div', class_='express_name')
                    bet_name = bet_name_div.find('b').get_text(' ', strip=True) if bet_name_div and bet_name_div.find(
                        'b') else ''
                else:
                    is_express = 'No'
                    bet_name = his_name.find('b').get_text(' ', strip=True) if his_name.find('b') else ''
            else:
                bet_name = ''
                is_express = 'No'

            # Extract coefficient and check its background color for status
            his_cof = item.find('div', class_='hisCof')
            coefficient = his_cof.get_text(strip=True) if his_cof else ''

            # Determine status from coefficient background color
            cof_style = his_cof.get('style', '') if his_cof else ''
            if 'background: #55C014' in cof_style:
                status = 'win'
            elif 'background: #ec3636' in cof_style:
                status = 'loss'
            elif 'background: #F3C000' in cof_style:
                status = 'refund'
            else:
                status = 'unsettled'

            # Extract additional details from the full properties table
            full_prop = item.find('div', class_='hisFullProp')
            bet_type = ''
            bet_selection = ''
            stake = ''
            potential_return = ''
            event_time = ''
            result = ''
            bet_name = ""
            if full_prop:
                # Extract all matches from <td class="ha">
                ha_tds = item.find_all('td', class_='ha')
                bet_names = []
                event_times = []
                for ha_td in ha_tds:
                    # Extract match name
                    event_name_elem = ha_td.find('span')
                    bet_name = event_name_elem.get_text(' ', strip=True) if event_name_elem else ''

                    # Extract event time (the last <b> tag inside)
                    time_elems = ha_td.find_all('b')
                    event_time = ''
                    if len(time_elems) > 1:
                        event_time = time_elems[-1].get_text(strip=True)
                    elif time_elems:
                        event_time = time_elems[0].get_text(strip=True)

                    bet_names.append(bet_name)
                    event_times.append(event_time)

                bet_name = ' | '.join(bet_names)
                event_time = ' | '.join(event_times)
                table_item = full_prop.find('table', class_='table_prop')
                table_item_rows = table_item.find_all('tr')
                selections = []

                for table_row in table_item_rows:
                    tds = table_row.find_all('td')
                    if len(tds) == 5:
                        ce1 = tds[2].get_text(' ', strip=True)
                        ce2 = tds[4].get_text(' ', strip=True)

                        selections.append(f"{ce1} ({ce2})")
                    elif len(tds) == 4:
                        result = tds[3].get_text('', strip=True)
                        result = result.replace("USD", "")
                        result = result.replace("Loss", "")
                        result = result.replace("Not paid out", "")

                bet_selection = " | ".join(selections)
                # Extract bet selection
                # selection_elem = full_prop.find('td', class_='ce', string=re.compile(r'.+'))
                # if selection_elem:
                #     bet_selection = selection_elem.get_text(strip=True)

                # Extract stake
                stake_elem = full_prop.find('td', class_='ce', string=re.compile(r'\d+\.?\d*\s*USD'))
                if stake_elem:
                    stake = stake_elem.get_text(strip=True)
                    stake = stake.replace("USD", "")

                # Extract result
                # result_elem = full_prop.find('td', string=re.compile(r'Result:'))
                # if result_elem:
                #     result_text = result_elem.get_text(strip=True)
                #     result = result_text.replace('Result:', '').strip()


            bet_data = {
                'bet_slip_number': bet_slip_number,
                'date_time': time_text,
                'bet_name': bet_name,
                'coefficient': coefficient,
                'is_express': is_express,
                'status': status,
                # 'bet_type': bet_type,
                'bet_selection': bet_selection,
                'stake': stake,
                'event_time': event_time,
                'result': result
            }

            bets_data.append(bet_data)

        except Exception as e:
            print(f"Error processing bet item: {e}")
            continue

    return bets_data


def save_to_csv(bets_data, filename='bets_data.csv'):
    """
    Save extracted bet data to CSV file
    """
    if not bets_data:
        print("No data to save")
        return

    fieldnames = [
        'bet_slip_number',
        'date_time',
        'bet_name',
        'coefficient',
        'is_express',
        'status',
        # 'bet_type',
        'bet_selection',
        'stake',
        'event_time',
        'result'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(bets_data)

    print(f"Data saved to {filename}")


# Example usage with the provided HTML
if __name__ == "__main__":
    # Read HTML content from file or variable
    with open('history_532141847.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Extract data
    bets_data = extract_bet_data(html_content)

    # Print extracted data
    print(f"Extracted {len(bets_data)} bets:")
    print("-" * 100)
    for i, bet in enumerate(bets_data, 1):
        print(f"Bet {i}:")
        print(f"  Slip: {bet['bet_slip_number']}")
        print(f"  Time: {bet['date_time']}")
        print(f"  Name: {bet['bet_name']}")
        print(f"  Odds: {bet['coefficient']}")
        print(f"  Express: {bet['is_express']}")
        print(f"  Status: {bet['status']}")
        # print(f"  Type: {bet['bet_type']}")
        print(f"  Selection: {bet['bet_selection']}")
        print(f"  Stake: {bet['stake']}")
        print(f"  Event: {bet['event_time']}")
        print(f"  Result: {bet['result']}")
        print()

    # Save to CSV
    save_to_csv(bets_data, "history_532141847.csv")