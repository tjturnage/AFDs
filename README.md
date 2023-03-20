
<table>
<tr>
<td>![](https://github.com/tjturnage/AFDs/blob/master/images/colab-icon.svg?raw=true)</td>
<td></td>
</tr>
</table>
![](https://github.com/tjturnage/AFDs/blob/master/images/colab-icon.svg?raw=true)

# AFDs

* Organizes a list of recent AFDs issued by an office for service assessment
* utilizes https://forecast.weather.gov/product.php?site=GRR&issuedby=GRR&product=AFD&format=ci&version=1&glossary=1

* grabs the latest  versions of AFDGRR
* extracts .UPDATE and .DISCUSSION sections from each version
* appends to a text file that viewable at : https://turnageweather.us/disc 

* Likely needs to be configured for offices that use .SHORT TERM and .LONG TERM sections since WFO GRR uses only DISCUSSION
