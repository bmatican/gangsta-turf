import httplib2
import json

class TokenExpiredException:
  pass

def get_places(token, center, distance):
  url = 'https://graph.facebook.com/search?type=place'
  url = '{}&access_token={}&distance={}&center={}'.format(
    url,
    token,
    distance,
    center,
  )
  places = []
  while True:
    _, content = httplib2.Http().request(url)
    content = json.loads(content)
    data = content.get('data')
    if data == None:
      raise TokenExpiredException
    if len(data) == 0:
      break
    url = content['paging']['next']
    for place in data:
      piece = {
        'id':place['id'],
        'name':place['name'],
        'latitude':place['location']['latitude'],
        'longitude':place['location']['longitude'],
        'category':place['category'],
        'category_list':place['category_list'],
      }
      places.append(piece)

  return places

static_categories = {
  'Food/beverages':1,
  'Arts & Entertainment':2,
  'Shopping Mall':3,
  'Company':4,
  'Non-profit organization':4,
  'Retail and consumer merchandise':3,
  'Public Places & Attractions':5,
  'Region':5,
  'Camp':5,
  'Pizza Place':1,
  'Adult Education':4,
  'Nightlife':2,
  'Landmark':5,
  'Organization':4,
  'Coffee Shop':1,
  'Shopping & Retail':3,
  'Airport Terminal':4,
  'Travel/leisure':4,
  'Spa':2,
  'Education':4,
  'Grocery Store':1,
  'Night Club':2,
  'Tourist Attraction':5,
  'Museum':5,
  'School':4,
  'Butcher':1,
  'Jazz Club':2,
  'Health Spa':2,
  'Theatre':2,
  'College & University':4,
  'Beauty Salon':2,
  'Pub':1,
  'Movie Theatre':2,
  'Public Transportation':4,
  'Train Station':4,
  'Public Square':5,
  'Hair Salon':2,
  'Shopping/retail':3,
  'Movie theater':2,
  'Deli':1,
  'Clothing Store':3,
  'Steakhouse':1,
  'Electronics Store':3,
  'Internet Cafe':3,
  'Spas/beauty/personal care':2,
  'Arts & Crafts Supply Store':3,
  'Retail and Consumer Merchandise':3,
  'Cafe':1,
  'Gym':2,
  'Adult Entertainment':2,
  'Outdoors':5,
  'Sports Venue & Stadium':5,
  'Sandwich Shop':1,
  'Swimming Pool':2,
  'Hotel':4,
  'Concert Venue':2,
  'Ice Cream Parlor':1,
  'Frozen Yogurt Shop':1,
  'Fish & Chips Shop':1,
  'Subway & Light Rail Station':5,
  'Casino':2,
  'Language School':4,
  'Concert venue':2,
  'Sports/recreation/activities':5,
  'Market':5,
  'Food/Beverages':1,
  'Resort':5,
  'Food & Grocery':1,
  'Museum/art gallery':2,
  'Health/beauty':2,
  'Brewery':1,
  'Highway':5,
  'Comedy Club':2,
  'Club':2,
  'Historical Place':5,
  'Social Club':2,
  'Non-Profit Organization':4,
  'Dance Club':2,
  'Food & Beverage Service & Distribution':1,
  'Dance Instruction':2,
  'Diner':1,
  'Travel & Transportation':5,
  'Computer Store':3,
  'Airport':4,
  'Corporate Office':4,
  'Monument':5,
  'Bridge':5,
  'Bands & Musicians':2,
  'Arts/entertainment/nightlife':2,
  'Airport Lounge':4,
  'Bakery':1,
  'Lodging':4,
  'Community & Government':4,
  'Performance Venue':2,
  'Health/Beauty':2,
}
