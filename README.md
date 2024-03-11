
<div align="right">
  </div>

# <img src="https://www.gstatic.com/lamda/images/favicon_v1_150160cddff7f294ce30.svg" width="35px" alt="Gemini Icon" /> Gemini API  <a href="https://pypi.org/project/python-gemini-api/"> <img alt="PyPI" src="https://img.shields.io/pypi/v/python-gemini-api?color=black"></a>



A *unofficial* Python wrapper, [python-gemini-api](https://pypi.org/project/python-gemini-api/), operates through reverse-engineering, utilizing cookie values to interact with [Google Gemini](https://gemini.google.com) for users struggling with frequent authentication problems or unable to authenticate via [Google Authentication](https://developers.google.com/identity/protocols/oauth2?hl=en). This repository is not expected to be updated frequently, and it will be modified for personal use. 

Collaborated competently with [Antonio Cheong](https://github.com/acheong08).

Please, check <img src="https://www.gstatic.com/lamda/images/favicon_v1_150160cddff7f294ce30.svg" width="15px" alt="Gemini Icon" />[HanaokaYuzu/Gemini-API](https://github.com/HanaokaYuzu/Gemini-API) first. 


<br>

## What is [Gemini](https://deepmind.google/technologies/gemini/#introduction)?

| [Paper](https://arxiv.org/abs/2312.11805) | [Official Website](https://deepmind.google/technologies/gemini/#introduction) | [Official API](https://aistudio.google.com/) | [API Documents](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini) |

Gemini is a family of generative AI models developed by Google DeepMind that is designed for multimodal use cases. The Gemini API gives you access to the Gemini Pro and Gemini Pro Vision models. In February 2024, Google's **Bard** service was changed to **Gemini**.

- [ Gemini API   ](#-gemini-api---)
  - [What is Gemini?](#what-is-gemini)
  - [Installation](#installation)
  - [Authentication](#authentication)
  - [Usage](#usage)
    - [# 01. Initialization](#-01-initialization)
    - [# 02. Generate content](#-02-generate-content)
    - [# 03. Text generation](#-03-text-generation)
    - [# 04. Image generation](#-04-image-generation)
    - [# 05. Retrieving Images from Gemini Responses](#-05-retrieving-images-from-gemini-responses)
    - [# 06. Generate content from images](#-06-generate-content-from-images)
    - [# 07. Generate content using Google Services](#-07-generate-content-using-google-services)
    - [# 08. Fix context setting rcid](#-08-fix-context-setting-rcid)
    - [# 09. Changing the Selected Response from 0 to n](#-09-changing-the-selected-response-from-0-to-n)
  - [Further](#further)
    - [Use rotating proxies](#use-rotating-proxies)
  - [More features](#more-features)
  - [Open-source LLM, Gemma](#open-source-llm-gemma)
    - [How to use Gemma](#how-to-use-gemma)
  - [FAQ](#faq)
  - [Sponsor](#sponsor)
  - [Issues](#issues)
  - [Contributors](#contributors)
  - [Contacts](#contacts)
  - [License](#license)
  - [References](#references)





<br>



## Installation
```bash
pip install python-gemini-api
```
```bash
pip install git+https://github.com/dsdanielpark/Gemini-API.git
```
For the updated version, use as follows:
```
pip install -q -U python-gemini-api
```
## Authentication
> [!NOTE]
> Cookies can change quickly. Don't reopen the same session or repeat prompts too often; they'll expire faster. If the cookie value doesn't export correctly, refresh the Gemini page and export again. Check this [sample cookie file](https://github.com/dsdanielpark/Gemini-API/blob/main/cookies.txt).
1. Visit https://gemini.google.com/
2. `F12` for browser console → `Session: Application` → `Cookies` → Copy the value of some working cookie sets. If it doesn't work, go to step 3.
    <details><summary>Some working cookie sets</summary>
    Cookies may vary by account or region. 
      
    First try `__Secure-1PSIDCC` alone. If it doesn't work, use `__Secure-1PSID` and `__Secure-1PSIDTS`. Still no success? Try these four cookies: `__Secure-1PSIDCC`, `__Secure-1PSID`, `__Secure-1PSIDTS`, `NID`. If none work, proceed to step 3 and consider sending the entire cookie file.
    
    </details>

3. *(Recommended)* Export Gemini site cookies via a browser extension (e.g., Chrome extension). Use [ExportThisCookies](https://chromewebstore.google.com/detail/exportthiscookie/dannllckdimllhkiplchkcaoheibealk), open, and copy the txt file contents.

<details><summary>Further: For manual collection or Required for a few users upon error</summary>

4. For manual cookie collection, refer to [this image](assets/cookies.pdf). Press F12 → Network → Send any prompt to gemini webui → Click the post address starting with "https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate" → Headers → Request Headers → Cookie → Copy and Reformat as JSON manually.
5. *(Required for a few users upon error)* If errors persist after manually collecting cookies, refresh the Gemini website and collect cookies again. If errors continue, some users may need to manually set the nonce value. To do this: Press F12 → Network → Send any prompt to gemini webui → Click the post address starting with "https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate" → Payload → Form Data → Copy the "at" key value. See [this image](assets/nonce_value.pdf) for reference.
</details>

<br>

## Usage


### # 01. Initialization
Please explicitly declare `cookies` in dict format. You can also enter the path to the file containing the cookie with `cookie_fp`.

```python
from gemini import Gemini

cookies = {
    "__Secure-1PSIDCC" : "value",
    "__Secure-1PSID" : "value",
    "__Secure-1PSIDTS" : "value",
    "NID" : "value",
    # Cookies may vary by account or region. Consider sending the entire cookie file.
  }

GeminiClient = Gemini(cookies=cookies)
# GeminiClient = Gemini(cookie_fp="folder/cookie_file.json") # Or use cookie file path
# GeminiClient = Gemini(auto_cookies=True) # Or use auto_cookies paprameter
```

> [!IMPORTANT]
>  **If the session connects successfully and `generate_content` runs well, CLOSE Gemini website.** If Gemini web stays open in the browser, cookies may expire faster.

<br>

### # 02. Generate content
To check regardless of the data type of the model output, return the response_dict argument. And use it appropriately.

```python
prompt = "Hello, Gemini. What's the weather like in Seoul today?"
response = GeminiClient.generate_content(prompt)
print(response.response_dict)
```
> [!IMPORTANT]
>  Once connected and generating valid content, **Be sure to CLOSE the gemini website or CLOSE your browser** for cookie stability. 


The output of the `generate_content` function is `GeminiModelOutput`, with the following structure:

**Properties of `GeminiModelOutput`:**
- *rcid*: returns the response choice id of the chosen candidate.
- *text*: returns the text of the chosen candidate.
- *web_images*: returns a list of web images from the chosen candidate.
- *generated_images*: returns a list of generated images from the chosen candidate.
- *response_dict*: returns the response dictionary, if available.



> [!NOTE]
> If the session fails to connect, works improperly, or terminates, returning an error, it is recommended to manually renew the cookies. The error is likely due to incorrect cookie values. Refresh or log out of Gemini web to renew cookies and try again. 

<br>

### # 03. Text generation
Returns text generated by Gemini.
```python
prompt = "Hello, Gemini. What's the weather like in Seoul today?"
response = GeminiClient.generate_content(prompt)
print(response.text)
```


<br>

### # 04. Image generation
Returns images generated by Gemini.


*Sync downloader*
```python
from gemini import Gemini, GeminiImage

response = GeminiClient.generate_content("Create illustrations of Seoul, South Korea.")
generated_images = response.generated_images # Check generated images [Dict]

GeminiImage.save_sync(generated_images, save_path="save_dir", cookies=cookies)

# You can use byte type image dict for printing images as follow:
# bytes_images_dict = GeminiImage.fetch_images_dict_sync(generated_images, cookies=cookies) # Get bytes images dict
# GeminiImage.save_images_sync(bytes_images_dict, path="save_dir", cookies=cookies) # Save to path
```

<details><summary>Display images in IPython</summary>
  
  ```python
  bytes_images_dict = GeminiImage.fetch_images_dict_sync(generated_images, cookies) # Get bytes images dict
  from IPython.display import display, Image
  import io
  
  for image_name, image_bytes in bytes_images_dict.items():
      print(image_name)
      image = Image(data=image_bytes)
      display(image)
  ```

</details>


*Async downloader*

```python
response = GeminiClient.generate_content("Create illustrations of Seoul, South Korea.")

generated_images = response.generated_images # Check generated images [Dict]

await GeminiImage.save(generated_images, "save_dir", cookies=cookies)
# image_data_dict = await GeminiImage.fetch_images_dict(generated_images, cookies=cookies)
# await GeminiImage.save_images(image_data_dict, "save_dir")
```


<details><summary>Async downloader wrapper</summary>

```
import asyncio
from gemini import Gemini, GeminiImage

async def save_generated_imagse(generated_imagse, save_path="save_dir", cookies=cookies):
    await GeminiImage.save(generated_imagse, save_path=save_path, cookies=cookies)

# Run the async function
if __name__ == "__main__":
    cookies = {"key" : "value"}
    generated_imagse = response.generated_imagse  
    asyncio.run(save_generated_imagse(generated_imagse, save_path="save_dir", cookies=cookies))
```

`GeminiImage.save` method logic

```
import asyncio
from gemini import Gemini, GeminiImage

async def save_generated_imagse(generated_imagse, save_path="save_dir", cookies=cookies):
    image_data_dict = await GeminiImage.fetch_images_dict(generated_imagse, cookies=cookies)  # Get bytes images dict asynchronously
    await GeminiImage.save_images(image_data_dict, save_path=save_path)  

# Run the async function
if __name__ == "__main__":
    cookies = {"key" : "value"}
    generated_imagse = response.generated_imagse  # Check response images [Dict]
    asyncio.run(save_generated_imagse(generated_imagse, save_path="save_dir", cookies=cookies))
```

</details>

> [!NOTE]
> Use GeminiImage for image processing. `web_images` works without cookies, but for images like `generated_image` from Gemini, pass cookies. Cookies are needed to download images from Google's storage. Check the response or use existing cookies variable.

<br>

### # 05. Retrieving Images from Gemini Responses
Returns images in response of Gemini.

*Sync downloader*
```python
from gemini import Gemini, GeminiImage

response = GeminiClient.generate_content("Please recommend a travel itinerary for Seoul.")
response_images = response.web_images # Check response images [Dict]

GeminiImage.save_sync(response_images, save_path="save_dir")

# You can use byte type image dict as follow:
# bytes_images_dict = GeminiImage.fetch_bytes_sync(response_images, cookies) # Get bytes images dict
# GeminiImage.save_images_sync(bytes_images_dict, path="save_dir") # Save to path
```
*Async downloader*
```python
response = GeminiClient.generate_content("Create illustrations of Seoul, South Korea.")

response_images = response.web_images # Check generated images [Dict]

await GeminiImage.save(response_images, "save_dir")
# image_data_dict = await GeminiImage.fetch_images_dict(response_images)
# await GeminiImage.save_images(image_data_dict, "save_dir")
```

<details><summary>Async downloader wrapper</summary>

```
import asyncio
from gemini import Gemini, GeminiImage

async def save_response_web_imagse(response_images, save_path="save_dir", cookies=cookies):
    await GeminiImage.save(response_images, save_path=save_path, cookies=cookies)

# Run the async function
if __name__ == "__main__":
    cookies = {"key" : "value"}
    response_images = response.web_images  
    asyncio.run(save_response_web_imagse(response_images, save_path="save_dir", cookies=cookies))
```

`GeminiImage.save` method logic

```
import asyncio
from gemini import Gemini, GeminiImage

async def save_response_web_imagse(response_images, save_path="save_dir", cookies=cookies):
    image_data_dict = await GeminiImage.fetch_images_dict(response_images, cookies=cookies)  # Get bytes images dict asynchronously
    await GeminiImage.save_images(image_data_dict, save_path=save_path)  

# Run the async function
if __name__ == "__main__":
    response_images = response.web_images  # Check response images [Dict]
    asyncio.run(save_response_web_imagse(response_images, save_path="save_dir", cookies=cookies))
```

</details>

<br>

### # 06. Generate content from images
Takes an image as input and returns a response.

```python
image = 'folder/image.jpg'
# image = open('folder/image.jpg', 'rb').read() # (jpeg, png, webp) are supported.

response = GeminiClient.generate_content("What does the text in this image say?", image=image)
response.response_dict
```

<br>

### # 07. Generate content using Google Services
To begin, you must link Google Workspace to activate this extension via the [Gemini web extension](https://gemini.google.com/extensions). Please refer to the [official notice](https://support.google.com/gemini/answer/13695044) and review the [privacy policies](https://support.google.com/gemini/answer/13594961?visit_id=638457301410420313-1578971242&p=privacy_help&rd=1) for more details.

*extention flags*
```
@Gmail, @Google Drive, @Google Docs, @Google Maps, @Google Flights, @Google Hotels, @YouTube
```
```python
response = GeminiClient.generate_content("@YouTube Search clips related with Google Gemini")
response.response_dict
```
<details><summary>Extension description</summary>
  
- Google Workspace
  - Services: @Gmail, @Google Drive, @Google Docs 
  - Description: Summarize, search, and find desired information quickly in your content for efficient personal task management.
  - Features: Information retrieval, document summarization, information categorization

- Google Maps
  - Service: @Google Maps
  - Description: Execute plans using location-based information. Note: Google Maps features may be limited in some regions.
  - Features: Route guidance, nearby search, navigation

- Google Flights
  - Service: @Google Flights
  - Description: Search real-time flight information to plan tailored travel itineraries.
  - Features: Holiday preparation, price comparison, trip planning

- Google Hotels
  - Service: @Google Hotels
  - Description: Search for hotels considering what matters most to you, like having a conversation with a friend.
  - Features: Packing for travel, sightseeing, special relaxation

- YouTube
  - Service: @YouTube
  - Description: Explore YouTube videos and ask questions about what interests you.
  - Features: Problem-solving, generating ideas, search, exploring topics
</details>

<br>


### # 08. Fix context setting rcid
You can specify a particular response by setting its Response Choice ID (RCID).

```python
# Generate content for the prompt "Give me some information about the USA."
response1 = GeminiClient.generate_content("Give me some information about the USA.")
# After reviewing the responses, choose the one you prefer and copy its RCID.
GeminiClient.rcid = "rc_xxxx"

# Now, generate content for the next prompt "How long does it take from LA to New York?"
response2 = GeminiClient.generate_content("How long does it take from LA to New York?")
```

<br>

### # 09. Changing the Selected Response from 0 to n
In Gemini, generate_content returns the first response. This may vary depending on length or sorting. Therefore, you can specify the index of the chosen response from 0 to n as follows. However, if there is only one response, revert it back to 0.
```python
from gemini import GeminiModelOutput
GeminiModelOutput.chosen = 1 # default is 0
response1 = GeminiClient.generate_content("Give me some information about the USA.")
```


## Further

### Use rotating proxies

If you want to **avoid blocked requests** and bans, then use [Smart Proxy by Crawlbase](https://crawlbase.com/docs/smart-proxy/?utm_source=github_ad&utm_medium=social&utm_campaign=bard_api). It forwards your connection requests to a **randomly rotating IP address** in a pool of proxies before reaching the target website. The combination of AI and ML make it more effective to avoid CAPTCHAs and blocks.

```python
# Get your proxy url at crawlbase https://crawlbase.com/docs/smart-proxy/get/
proxy_url = "http://xxxxx:@smartproxy.crawlbase.com:8012" 
proxies = {"http": proxy_url, "https": proxy_url}

GeminiClient = Gemini(cookies=cookies, proxies=proxies, timeout=30)
GeminiClient.generate_content("Hello, Gemini. Give me a beautiful photo of Seoul's scenery.")
```





<br>

## [More features](https://github.com/dsdanielpark/Gemini-API/blob/main/documents/README_DEV.md)
Explore additional features in [this document](https://github.com/dsdanielpark/Gemini-API/blob/main/documents/README_DEV.md).

<br>


## Open-source LLM, [Gemma](https://huggingface.co/google/gemma-7b)
If you have sufficient GPU resources, you can download weights directly instead of using the Gemini API to generate content. Consider Gemma, an open-source model **available for on-premises use**.

[Gemma](https://huggingface.co/google/gemma-7b) models are Google's lightweight, advanced text-to-text, decoder-only language models, derived from Gemini research. Available in English, they offer open weights and variants, ideal for tasks like question answering and summarization. Their small size enables deployment in resource-limited settings, broadening access to cutting-edge AI. For more infomation, visit [Gemma-7b](https://huggingface.co/google/gemma-7b) model card.

### How to use Gemma
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("google/gemma-7b")
model = AutoModelForCausalLM.from_pretrained("google/gemma-7b")

input_text = "Write me a poem about Machine Learning."
input_ids = tokenizer(input_text, return_tensors="pt")

outputs = model.generate(**input_ids)
print(tokenizer.decode(outputs[0]))
```

<br>


## [FAQ](https://github.com/dsdanielpark/Gemini-API/blob/main/documents/README_FAQ.md)
You can find most help on the [FAQ](https://github.com/dsdanielpark/Gemini-API/blob/main/documents/README_FAQ.md) and [Issue](https://github.com/dsdanielpark/Gemini-API/issues) pages. Alternatively, utilize the official Gemini API at [Google AI Studio](https://ai.google.dev/tutorials/ai-studio_quickstart).


## Sponsor
Use [Crawlbase](https://crawlbase.com/) API for efficient data scraping to train AI models, boasting a 98% success rate and 99.9% uptime. It's quick to start, GDPR/CCPA compliant, supports massive data extraction, and is trusted by 70k+ developers.

            
## [Issues](https://github.com/dsdanielpark/Gemini-API/issues)
Sincerely grateful for any reports on new features or bugs. Your valuable feedback on the code is highly appreciated. Frequent errors may occur due to changes in Google's service API interface. Both [Issue reports](https://github.com/dsdanielpark/Gemini-API/issues) and [Pull requests](https://github.com/dsdanielpark/Gemini-API/pulls) contributing to improvements are always welcome. We strive to maintain an active and courteous open community.


## Contributors
We would like to express our sincere gratitude to all the contributors.

Contributors to the [Bard API](https://github.com/dsdanielpark/Bard-API/) and [Gemini API](https://github.com/dsdanielpark/Gemini-API/).

<a href="https://github.com/dsdanielpark/Bard_API/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=dsdanielpark/Bard_API" />
</a>

<br>

<details><summary>Further development potential</summary>
  
- [ ] `refactoring`
- [x] `gemini/core`: httpx.session
  - [x] `messages`
      - [x] `content`
        - [x] `text`  
          - [x] `parsing`
        - [x] `image`
          - [x] `parsing`
      - [x] `response format structure class`
      - [ ] `tool_calls`
  - [ ] `third party`
    - [ ] `replit`
    - [ ] `google tools`
- [ ] `gemini/client`: httpx.AsyncClient
  - [ ] `messages`
      - [ ] `content`
        - [ ] `text`  
          - [ ] `parsing`
        - [ ] `image`
          - [ ] `parsing`
      - [ ] `response format structure class`
      - [ ] `tool_calls`
  - [ ] `third party`
    - [ ] `replit`
    - [ ] `google tools`   
</details>

## Contacts

Core maintainers:
- [Antonio Cheong](https://github.com/acheong08) / teapotv8@proton.me <br>
- [Daniel Park](https://github.com/DSDanielPark) / parkminwoo1991@gmail.com
 


## License
[MIT](https://opensource.org/license/mit/) license, 2024. We hereby strongly disclaim any explicit or implicit legal liability related to our works. Users are required to use this package responsibly and at their own risk. This project is a personal initiative and is not affiliated with or endorsed by Google. It is recommended to use Google's official API.


## References
[1] Github: [acheong08/Bard](https://github.com/acheong08/Bard) <br>
[2] Github: [dsdanielpark/Bard-API](https://github.com/dsdanielpark/Bard-API) <br>
[3] GitHub: [HanaokaYuzu/Gemini-API](https://github.com/HanaokaYuzu/Gemini-API) <br>
[4] Github: [GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai) <br>
[5] WebSite: [Google AI Studio](https://ai.google.dev/tutorials/ai-studio_quickstart) <br>

> *Warning*
Users bear all legal responsibilities when using the GeminiAPI package, which offers easy access to Google Gemini for developers. This unofficial Python package isn't affiliated with Google and may lead to Google account restrictions if used excessively or commercially due to its reliance on Google account cookies. Frequent changes in Google's interface, Google's API policies, and your country/region, as well as the status of your Google account, may affect functionality. Utilize the issue page and discussion page.

<br>


