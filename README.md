
Run this AFD script in Google Colab:
https://github.com/tjturnage/AFDs/blob/master/AFDs.ipynb

On that page, click this icon:
![svg](https://github.com/tjturnage/AFDs/blob/master/images/colab-icon.svg?raw=true)

You'll get a warning that it's external that you may disregard.

Once in the notebook, you'll need to run each "cell" in order by clicking its arrow on the left:
![svg](https://github.com/tjturnage/AFDs/blob/master/images/run_complete_crop.png?raw=true)

<table>
<tr>
<td></td>
<td></td>
</tr>
</table>


# AFDs

* Organizes a list of recent AFDs issued by an office for service assessment
* utilizes https://forecast.weather.gov/product.php?site=GRR&issuedby=GRR&product=AFD&format=ci&version=1&glossary=1

* grabs the latest  versions of AFDGRR
* extracts .UPDATE and .DISCUSSION sections from each version
* appends to a text file that viewable at : https://turnageweather.us/disc 

* Likely needs to be configured for offices that use .SHORT TERM and .LONG TERM sections since WFO GRR uses only DISCUSSION
