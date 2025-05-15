import requests
import re
import base58
from django.shortcuts import render, redirect
from solders.pubkey import Pubkey
from .models import ChatMessage

def get_metadata_pda(mint_address):
    program_id = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")
    seeds = [b'metadata', bytes(program_id), bytes(Pubkey.from_string(mint_address))]
    pda, _ = Pubkey.find_program_address(seeds, program_id)
    return str(pda)

def get_token_data(address):
    try:
        if not re.match(r'^[1-9A-HJ-NP-Za-km-z]{43,44}$', address):
            return {'error': 'Invalid token address format'}

        token_info = {}
        
        # Try Jupiter's token list
        try:
            token_list = requests.get('https://token.jup.ag/all').json()
            token_info = next((t for t in token_list if t['address'] == address), {})
        except:
            pass

        # Try Metaplex metadata
        if not token_info.get('name'):
            try:
                metadata_address = get_metadata_pda(address)
                response = requests.post(
                    'https://api.mainnet-beta.solana.com',
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getAccountInfo",
                        "params": [metadata_address, {"encoding": "base64"}]
                    }
                )
                account_data = response.json()['result']['value']
                if account_data:
                    data = base58.b58decode(account_data['data'][0])
                    name = data[1:33].decode('utf-8').strip('\x00')
                    symbol = data[33:43].decode('utf-8').strip('\x00')
                    token_info.update({'name': name, 'symbol': symbol})
            except:
                pass

        # Get price data
        price_value = 0
        vs_token_symbol = 'USD'
        try:
            price_response = requests.get(
                f'https://lite-api.jup.ag/price/v2?ids={address}',
                headers={'Accept': 'application/json'}
            )
            price_data = price_response.json()
            price_entry = price_data.get('data', {}).get(address) or next(iter(price_data.get('data', [])), {})
            price_value = float(price_entry.get('price', 0))
            vs_token_symbol = price_entry.get('vsTokenSymbol', 'USD')
        except:
            pass

        # Get supply data
        supply_value = 0
        try:
            supply_response = requests.post(
                'https://api.mainnet-beta.solana.com',
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenSupply",
                    "params": [address]
                }
            )
            supply_data = supply_response.json()
            if supply_data.get('result'):
                supply_info = supply_data['result']['value']
                supply_value = int(supply_info['amount']) / (10 ** supply_info['decimals'])
        except:
            pass

        return {
            'address': address,
            'name': token_info.get('name', 'Unknown Token'),
            'symbol': token_info.get('symbol', 'UNKNOWN'),
            'price': price_value,
            'vsTokenSymbol': vs_token_symbol,
            'market_cap': price_value * supply_value,
            'supply': supply_value
        }

    except Exception as e:
        return {'error': str(e)}

def join_room(request):
    error = None
    if request.method == 'POST':
        token_address = request.POST.get('token_address', '').strip()
        
        # Extract the first valid Solana address from the input using regex
        match = re.search(r'([1-9A-HJ-NP-Za-km-z]{43,44})', token_address)
        if not match:
            error = "Invalid token address format (must be 44 characters)"
        else:
            clean_address = match.group(1)
            return redirect('chat_room', room_name=clean_address)
    
    return render(request, 'chat/join_room.html', {'error': error})

def chat_room(request, room_name):
    # Get username from session
    username = request.session.get('username', 'Anonymous')
    token_data = get_token_data(room_name)
    messages = ChatMessage.objects.filter(room=room_name).order_by('-timestamp')[:50]
    
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'token_data': token_data,
        'messages': messages,
        'username': username  # Pass to template
    })