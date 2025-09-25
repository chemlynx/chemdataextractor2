"""
Scripts for evaluation.

Usage::

    tg_eval = Evaluate(GlassTransitionTemperature, folder=r'./scraped', n_papers_limit=200, n_records_limit=200)
    tg_eval.eval()
    tg_eval.print_results()

Here, `GlassTransitionTemperature` is a ChemDataExtractor model and `folder` is the folder with papers to be analyzed.
`n_papers_limit` and `n_records_limit` are the minima required for termination of the evaluation.
Both must be satisfied.

To continue the evaluation if interrupted::

    with open("evaluation.pickle", "rb") as pickle_file:
        tg_eval = pickle.load(pickle_file)
    tg_eval.eval()
    tg_eval.print_results()

A log file capturing the interactive terminal output and input is maintained in `evaluation-log.txt`.
The latest results are updated in 1results.txt`.

"""

import os
import pickle
import sys
import webbrowser
from pathlib import Path
from pprint import pprint

from .. import Document


class Logger:
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("evaluation-log.txt", "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()


sys.stdout = Logger()


def documents(folder):
    """Yields CDE documents for a given folder"""
    folder_path = Path(folder)
    for file_path in sorted(folder_path.iterdir()):
        if not file_path.name.startswith("."):
            fb = open(file_path, "rb")
            doc = Document.from_file(fb)
            fb.close()
            yield doc, str(file_path)


def records(cde_doc, models):
    """Yields CDE records for a given CDE document and CDE model"""
    cde_doc.models = []
    for m in models:
        cde_doc.models.append(m)
    recs = cde_doc.records
    if recs:
        for record in recs:
            if isinstance(record, tuple(models)):
                yield record


class Evaluate:
    """Main class for evaluation of a particular model on a given corpus of literature"""

    def __init__(
        self,
        models,
        folder=r"./",
        n_papers_limit=200,
        n_records_limit=200,
        show_website=True,
        _automated=False,
    ):
        self._automated = _automated
        self.show_website = show_website
        self.folder = folder
        self.models = models
        self.n_papers_limit = n_papers_limit
        self.n_records_limit = n_records_limit
        self.n_papers = len(list(Path(folder).iterdir()))

        # number of paper that was last evaluated
        self.n_paper = -1

        # number of records found in the corpus
        self.n_unidentified = 0
        self.n_records = 0

        # correct records
        self.nc = 0
        self.nc_autosentence = 0
        self.nc_template = 0
        self.nc_snowball = 0
        self.nc_table = 0
        self.nc_definition = 0

        # correct and duplicate
        self.ncd = 0
        self.ncd_autosentence = 0
        self.ncd_template = 0
        self.ncd_snowball = 0
        self.ncd_table = 0
        self.ncd_definition = 0

        # wrong records
        self.nw = 0
        self.nw_cer = 0
        self.nw_autosentence = 0
        self.nw_template = 0
        self.nw_snowball = 0
        self.nw_table = 0
        self.nw_table_tde = 0
        self.nw_table_cde = 0
        self.nw_definition = 0
        self.nw_interdependency = 0
        self.nw_other = 0

        # list containing description of other failures
        self.w_other = []

    def eval(self):
        """Evaluates the corpus"""
        with open("results.txt", "w", encoding="utf-8") as f:
                for n_paper, doc in enumerate(documents(self.folder)):
                # if loaded from pickle, eval will start where left of
                if n_paper <= self.n_paper and self.n_paper >= 0:
                    continue

                print(f"Paper {n_paper}/{self.n_papers}")
                print(f"DOI:       {doc[0].metadata.doi}")
                print(f"Journal:   {doc[0].metadata.journal}")
                print(f"Publisher: {doc[0].metadata.publisher}")
                print(f"PDF Url:   {doc[0].metadata.pdf_url}")
                print(f"HTML Url:  {doc[0].metadata.html_url}")

                doc_opened = False
                for record in records(doc[0], self.models):
                    if record.is_unidentified:
                        self.n_unidentified += 1
                    if not record.is_unidentified:
                        self.n_records += 1

                        print(f"Record {self.n_records}: \n")
                        pprint(record.serialize())
                        print(f"    Method:  {record.record_method}")
                        print(f"    Updated: {record.updated}")

                        if not doc_opened and self.show_website:
                            webbrowser.open(doc[0].metadata.html_url)
                            doc_opened = True
                        if self._automated:
                            input_cw = 0
                        else:
                            input_cw = input(
                                "    Correct (0)   OR   Correct and duplicate (1)   OR   Wrong (2)   OR   SKIP (3)?"
                            )
                            try:
                                input_cw = int(input_cw)
                            except ValueError:
                                input_cw = input(
                                    "    Correct (0)   OR   Correct and duplicate (1)   OR   Wrong (2)   OR   SKIP (3)?"
                                )
                                input_cw = int(input_cw)
                                print(f"         {input_cw}")

                        if input_cw == 0:
                            self.nc += 1

                            if record.record_method == "AutoSentenceParser":
                                self.nc_autosentence += 1
                            elif (
                                record.record_method == "QuantityModelTemplateParser"
                                or record.record_method == "MultiQuantityModelTemplateParser"
                            ):
                                self.nc_template += 1
                            elif record.record_method == "Snowball":
                                self.nc_snowball += 1
                            elif record.record_method == "AutoTableParser":
                                self.nc_table += 1

                            if record.updated:
                                self.nc_definition += 1
                                # print(doc[0].definitions)

                        if input_cw == 1:
                            self.ncd += 1

                            if record.record_method == "AutoSentenceParser":
                                self.ncd_autosentence += 1
                            elif (
                                record.record_method == "QuantityModelTemplateParser"
                                or record.record_method == "MultiQuantityModelTemplateParser"
                            ):
                                self.ncd_template += 1
                            elif record.record_method == "Snowball":
                                self.ncd_snowball += 1
                            elif record.record_method == "AutoTableParser":
                                self.ncd_table += 1

                            if record.updated:
                                self.ncd_definition += 1

                        if input_cw == 2:
                            self.nw += 1

                            input_w = input(
                                "    CER (1), AutoSentence (2), AutoTemplate (3), Snowball (4), Table (5), Definition update (6), Interdependency resolution (7), Other (8)? "
                            )
                            try:
                                input_w = int(input_w)
                            except ValueError:
                                input_w = input(
                                    "    CER (1), AutoSentence (2), AutoTemplate (3), Snowball (4), Table (5), Definition update (6), Interdependency resolution (7), Other (8)? "
                                )
                                input_w = int(input_w)
                            print(f"         {input_w}")

                            if input_w == 1:
                                self.nw_cer += 1
                            elif input_w == 2:
                                self.nw_autosentence += 1
                            elif input_w == 3:
                                self.nw_template += 1
                            elif input_w == 4:
                                self.nw_snowball += 1
                            elif input_w == 5:
                                self.nw_table += 1
                            elif input_w == 6:
                                self.nw_definition += 1
                            elif input_w == 7:
                                self.nw_interdependency += 1
                            elif input_w == 8:
                                self.nw_other += 1

                            if input_w == 5:
                                for table in doc[0].tables:
                                    print(table.tde_table)
                                    table.tde_table.print()
                                    print(table.tde_table.history)

                                input_w_table = input("    TDE (1) or CDE (2)?")
                                try:
                                    input_w_table = int(input_w_table)
                                except ValueError:
                                    input_w_table = input("    TDE (1) or CDE (2)?")
                                    input_w_table = int(input_w_table)
                                print(f"         {input_w_table}")

                                if input_w_table == 1:
                                    self.nw_table_tde += 1
                                elif input_w_table == 2:
                                    self.nw_table_cde += 1

                            if input_w == 8:
                                input_w_other = input("    Describe: ")
                                self.w_other.append(input_w_other)
                                print(f"             {input_w_other}")

                        if input_cw == 3:
                            continue

                    if self.limits_reached:
                        break

                self.n_paper = n_paper
                with open("evaluation.pickle", "wb") as pickling_file:
                    pickle.dump(self, pickling_file)
                f.seek(0)
                f.truncate()
                self.print_results(destination=f)
                f.flush()

                if self.limits_reached:
                    break
                print("")

    @property
    def limits_reached(self):
        return bool(
            self.n_paper + 1 >= self.n_papers_limit and self.n_records >= self.n_records_limit
        )

    def print_results(self, destination=sys.stdout):
        """Prints the results of evaluation"""
        print("===================================================", file=destination)
        print("                  RESULTS                          ", file=destination)
        print("===================================================", file=destination)
        print("", file=destination)
        print(f"Number of papers tested: {self.n_paper + 1}", file=destination)
        print(f"Unidentified records: {self.n_unidentified}", file=destination)
        print(
            f"Total records (correct+wrong+skipped): {self.n_records}",
            file=destination,
        )
        print("", file=destination)
        print(f"Correct records: {self.nc}", file=destination)
        print(
            f"    Correct AutoSentence: {self.nc_autosentence}",
            file=destination,
        )
        print(f"    Correct Template:     {self.nc_template}", file=destination)
        print(f"    Correct Snowball:     {self.nc_snowball}", file=destination)
        print(f"    Correct AutoTable:    {self.nc_table}", file=destination)
        print(f"    Correct Definition:   {self.nc_definition}", file=destination)
        print("", file=destination)
        print(f"Correct and duplicate records: {self.ncd}", file=destination)
        print(
            f"    Duplicate AutoSentence: {self.ncd_autosentence}",
            file=destination,
        )
        print(f"    Duplicate Template:     {self.ncd_template}", file=destination)
        print(f"    Duplicate Snowball:     {self.ncd_snowball}", file=destination)
        print(f"    Duplicate AutoTable:    {self.ncd_table}", file=destination)
        print(
            f"    Duplicate Definition:   {self.ncd_definition}",
            file=destination,
        )
        print("", file=destination)
        print(f"Wrong records: {self.nw}", file=destination)
        print(f"    Wrong CER:          {self.nw_cer}", file=destination)
        print(f"    Wrong AutoSentence: {self.nw_autosentence}", file=destination)
        print(f"    Wrong Template:     {self.nw_template}", file=destination)
        print(f"    Wrong Snowball:     {self.nw_snowball}", file=destination)
        print(f"    Wrong AutoTable:    {self.nw_table}", file=destination)
        print(f"        TDE:            {self.nw_table_tde}", file=destination)
        print(f"        CDE:            {self.nw_table_cde}", file=destination)
        print(f"    Wrong Definition:   {self.nw_definition}", file=destination)
        print(
            f"    W. Interdependency: {self.nw_interdependency}",
            file=destination,
        )
        print(f"    Other:              {self.nw_other}", file=destination)
        for item in self.w_other:
            print(f"        {item}", file=destination)
        print("", file=destination)
        print(" PRECISION ", file=destination)
        print("===========", file=destination)
        print("", file=destination)
        if (self.nc + self.nw) != 0:
            print(
                f"Total precision                      = {self.nc / (self.nc + self.nw):4.2f}, {self.nc}/{self.nc + self.nw}",
                file=destination,
            )
        if (self.nc + self.nw - self.nw_autosentence) != 0:
            print(
                f"Precision without AutoSentenceParser = {(self.nc - self.nc_autosentence) / (self.nc + self.nw - self.nw_autosentence):4.2f}, {self.nc - self.nc_autosentence}/{self.nc + self.nw - self.nw_autosentence}   ---> Approximation",
                file=destination,
            )
        if (self.nc + self.nw - self.nw_cer) != 0:
            print(
                f"Precision without CER Errors         = {self.nc / (self.nc + self.nw - self.nw_cer):4.2f}, {self.nc}/{self.nc + self.nw - self.nw_cer}",
                file=destination,
            )
        if (self.nc + self.nw - self.nw_autosentence - self.nw_cer) != 0:
            print(
                "Precision without AutoS. and CER     = {:4.2f}, {}/{}".format(
                    (self.nc - self.nc_autosentence)
                    / (self.nc + self.nw - self.nw_autosentence - self.nw_cer),
                    (self.nc - self.nc_autosentence),
                    (self.nc + self.nw - self.nw_autosentence - self.nw_cer),
                ),
                file=destination,
            )
        if (self.nc_table + self.nw_table) != 0:
            print(
                f"Table Precision                      = {self.nc_table / (self.nc_table + self.nw_table):4.2f}, {self.nc_table}/{self.nc_table + self.nw_table}",
                file=destination,
            )
        if self.nw_table != 0:
            print(
                f"   TDE Errors within Table Errors    = {self.nw_table_tde / self.nw_table:4.2f}, {self.nw_table_tde}/{self.nw_table}",
                file=destination,
            )
            print(
                f"   CDE Errors within Table Errors    = {self.nw_table_cde / self.nw_table:4.2f}, {self.nw_table_cde}/{self.nw_table}",
                file=destination,
            )
        if (self.nc_template + self.nw_template) != 0:
            print(
                f"Template Precision                   = {self.nc_template / (self.nc_template + self.nw_template):4.2f}, {self.nc_template}/{self.nc_template + self.nw_template}",
                file=destination,
            )
        if (self.nc_snowball + self.nw_snowball) != 0:
            print(
                f"Snowball Precision                   = {self.nc_snowball / (self.nc_snowball + self.nw_snowball):4.2f}, {self.nc_snowball}/{self.nc_snowball + self.nw_snowball}",
                file=destination,
            )
        if (self.nc_definition + self.nw_definition) != 0:
            print(
                f"Definitions update Precision         = {self.nc_definition / (self.nc_definition + self.nw_definition):4.2f}, {self.nc_definition}/{self.nc_definition + self.nw_definition}",
                file=destination,
            )
        if self.nw != 0:
            print(
                f"Percentage of 'other' errors         = {self.nw_other / self.nw:4.2f}, {self.nw_other}/{self.nw}",
                file=destination,
            )
