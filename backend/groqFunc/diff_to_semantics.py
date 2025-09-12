from groq import Groq
import os

task = """
Using the examples provided above, your objective is to extract the key tags related to what are the semantics of the 2 strings within each list element of the list of conflicts (understand the nested structure clearly!) from within the stringed json input. Then follow the output and return the tags as a list of strings with the same order.
"""

example1_input = """
{
	"conflicts" : 
	[
		[
			"After confirmation, either Party may terminate the Employment with one (1) month notice.",
			"After confirmation, either Party may terminate the Employment with one (1) year notice."
		],
		[
			"On Termination Date, the Employee must return all Company property which is in his possession. The Employee will be liable to reimburse the Company for any loss of or damage to such property, except for fair wear and tear. The amount of such loss or damage shall be deducted from his final salary in the limits provided by the applicable legislation.",
			"On Termination Date, the Employee can retain all Company property which are in his possession."
		],
		[
			"No clause matched",
			"Drinks Coffee instead of Tea"
		]
	]
}
"""

example1_output = "{'semantics': [['After confirmation', 'terminate employment', 'notice'], ['On Termination Date', 'Employee', 'company property', 'in possession'], ['Drinks']]}"

example2_input = """
{
	"conflicts" : 
	[
		[
			"Is guilty of any gross misconduct affecting the business of the Company;",
			"Is guilty of any gross misconduct affecting the business or culture of the Company;"
		],
        	[
			"Is absent from work without the permission of the Company;",
			"No clause matched"
		],
		[
			"No clause matched",
			"Attempts to or is caught defrauding the Company card;"
		],
	]
}
"""

example2_output = "{'semantics': [['gross misconduct', 'affecting', 'company'], ['absent', 'from work', 'without permission'], ['attempts', 'caught', 'defrauding', 'Company card']]}"

def main(input):
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY")
    )
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {
                "role": "user",
                "content": f"### Example 1\ninput:\n{example1_input}\noutput:\n{example1_output}\n\n### Example 2\ninput:\n{example2_input}\noutput:\n{example2_output}\n\n### Task\n{task}\n\ninput:\n{input}"
            },
        ],
        temperature=0.2,
        max_completion_tokens=4096,
        top_p=0.9,
        stream=False,
        response_format={"type": "json_object"},
        stop=None,
    )

    return completion.choices[0].message.content

if __name__ == "__main__":
    input = """
    {
        "conflicts" : 
        [
                [
                        "Is guilty of any gross misconduct affecting the business 
    of the Company;",
                        "Is guilty of any gross misconduct affecting the business 
    or the culture of the Company;"
                ],
                [
                        "Is, in the reasonable opinion of the Board, negligent and incompetent in the performance of his duties; or",
                        "No clause matched"
                ],
                [
                        "No clause matched",
                        "Sucks at doing his job"
                ],
                [
                        "No clause matched",
                        "Drinks coffee over tea"
                ]
        ]
    }
    """
    main(input)
